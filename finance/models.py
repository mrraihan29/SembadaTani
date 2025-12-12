from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum

# Import dari apps lain
from warehouse.models import Distribution
from core.models import FertilizerPrice, User

class Invoice(models.Model):
    """
    Tagihan (Piutang) yang terbit otomatis dari Penyaluran.
    Menggunakan konsep 'Snapshot Price' agar data historis aman.
    """
    STATUS_CHOICES = [
        ('UNPAID', 'Belum Lunas'),
        ('PARTIAL', 'Dicicil (Sebagian)'),
        ('PAID', 'Lunas'),
    ]

    # Relasi OneToOne: Satu Penyaluran = Satu Invoice
    distribution = models.OneToOneField(Distribution, on_delete=models.CASCADE, related_name='invoice', verbose_name="Ref Penyaluran")
    
    invoice_number = models.CharField(max_length=50, blank=True, unique=True, verbose_name="No. Invoice")
    created_at = models.DateField(default=timezone.now, verbose_name="Tanggal Tagihan")
    due_date = models.DateField(verbose_name="Jatuh Tempo Pembayaran")
    
    # Snapshot Data (Disimpan sebagai angka mati, bukan rumus)
    tonnage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tonase (Ton)")
    price_per_ton = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Harga/Ton (Saat Transaksi)")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total Tagihan")
    
    # Kolom auto-update (Jangan diedit manual)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Sudah Dibayar")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNPAID')

    def calculate_status(self):
        """Fungsi Robot: Update status lunas/belum berdasarkan pembayaran"""
        # Hitung total pembayaran yang masuk di tabel Payment
        total_bayar = self.payments.aggregate(Sum('amount'))['amount__sum'] or 0
        self.amount_paid = total_bayar

        if self.amount_paid >= self.total_amount:
            self.status = 'PAID'
        elif self.amount_paid > 0:
            self.status = 'PARTIAL'
        else:
            self.status = 'UNPAID'
        
        # Simpan perubahan status & amount_paid saja (biar efisien)
        self.save(update_fields=['amount_paid', 'status'])

    def save(self, *args, **kwargs):
        # LOGIKA PEMBUATAN BARU
        if self.pk is None:
            # 1. Ambil data dari Distribution
            self.tonnage = self.distribution.tonnage_sent
            
            # 2. Cari Harga Master yang berlaku untuk jenis pupuk ini
            pupuk_type = self.distribution.sales_order.fertilizer_type
            try:
                price_obj = FertilizerPrice.objects.get(fertilizer_type=pupuk_type)
                self.price_per_ton = price_obj.price_per_ton
            except FertilizerPrice.DoesNotExist:
                raise ValidationError(f"Harga untuk pupuk {pupuk_type} belum disetting di Master Data!")

            # 3. Hitung Total (Kunci Data)
            self.total_amount = self.tonnage * self.price_per_ton

            # 4. Generate No Invoice (INV/TGL/ID_DIST)
            # Kita perlu save dulu biar dapet ID, tapi karena ini OneToOne dengan Distribution,
            # kita bisa pakai ID distribution sebagai referensi
            date_str = self.created_at.strftime('%Y%m%d')
            self.invoice_number = f"INV/{date_str}/{self.distribution.id:04d}"

            # 5. Set Default Jatuh Tempo (Misal: 14 hari dari kirim)
            if not self.due_date:
                self.due_date = self.created_at + timezone.timedelta(days=14)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.distribution.kios.name} (Sisa: {self.total_amount - self.amount_paid:,})"

    class Meta:
        verbose_name = "Invoice Piutang"
        verbose_name_plural = "Data Invoice Piutang"


class Payment(models.Model):
    """
    Pencatatan Pembayaran (Bisa Nyicil).
    Setiap simpan, akan memanggil 'Robot' di Invoice untuk update status lunas.
    """
    METHOD_CHOICES = [('TRANSFER', 'Transfer Bank'), ('CASH', 'Tunai'), ('GIRO', 'Giro')]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name="Bayar Invoice No")
    payment_date = models.DateField(default=timezone.now, verbose_name="Tanggal Bayar")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Jumlah Bayar (Rp)")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='TRANSFER')
    
    proof_image = models.ImageField(upload_to='payments/', blank=True, null=True, verbose_name="Bukti Transfer")
    notes = models.TextField(blank=True, verbose_name="Catatan")
    
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Diterima Oleh")

    def clean(self):
        # Validasi: Tidak boleh bayar melebihi sisa hutang!
        # Hitung sisa hutang saat ini
        sisa_hutang = self.invoice.total_amount - self.invoice.amount_paid
        
        # Jika ini edit data lama, kita harus exclude diri sendiri dulu dari perhitungan
        if self.pk:
            current_self = Payment.objects.get(pk=self.pk)
            sisa_hutang += current_self.amount

        if self.amount > sisa_hutang:
            raise ValidationError(f"Kelebihan Bayar! Sisa hutang hanya Rp {sisa_hutang:,.0f}")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # TRIGGER ROBOT: Suruh Invoice hitung ulang statusnya
        self.invoice.calculate_status()

    def delete(self, *args, **kwargs):
        # Kalau pembayaran dihapus, status invoice harus dihitung ulang (mundur)
        invoice_ref = self.invoice
        super().delete(*args, **kwargs)
        invoice_ref.calculate_status()

    def __str__(self):
        return f"Bayar Rp {self.amount:,.0f} ({self.invoice.distribution.kios.name})"

    class Meta:
        verbose_name = "Riwayat Pembayaran"
        verbose_name_plural = "Riwayat Pembayaran"