from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.apps import apps # PENTING: Untuk panggil modul finance

# Import dari apps lain
from core.models import Regency, Kios, Armada

class SalesOrder(models.Model):
    """
    INBOUND: Pencatatan Penebusan Stok dari Holding.
    """
    PUPUK_CHOICES = [('UREA', 'UREA'), ('NPK', 'NPK')]
    STATUS_CHOICES = [
        ('AMAN', 'Aman'),
        ('WARNING', 'Mendekati Jatuh Tempo'),
        ('OVERDUE', 'Jatuh Tempo!'),
        ('HABIS', 'Stok Habis')
    ]

    regency = models.ForeignKey(Regency, on_delete=models.CASCADE, verbose_name="Kabupaten")
    so_code = models.CharField(max_length=50, unique=True, verbose_name="Kode SO / Booking")
    fertilizer_type = models.CharField(max_length=10, choices=PUPUK_CHOICES, verbose_name="Jenis Pupuk")
    district_allocation = models.CharField(max_length=100, verbose_name="Alokasi Kecamatan")
    
    initial_tonnage = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tonase Awal")
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sisa Stok")
    
    input_date = models.DateField(default=timezone.now, verbose_name="Tanggal Penebusan")
    due_date_gudang = models.DateField(blank=True, null=True, verbose_name="Jatuh Tempo Gudang")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AMAN', editable=False)

    def save(self, *args, **kwargs):
        # Cek apakah ini data baru (sebelum disimpan, PK masih None)
        is_new = self.pk is None
        
        # 1. Otomatis hitung jatuh tempo (+21 hari) jika belum ada
        if not self.due_date_gudang:
            self.due_date_gudang = self.input_date + timedelta(days=21)
        
        # 2. Inisialisasi Stok Awal
        if self.current_stock is None:
            self.current_stock = self.initial_tonnage
            
        # 3. Update Status otomatis
        if self.current_stock <= 0:
            self.status = 'HABIS'
        else:
            today = timezone.now().date()
            if self.due_date_gudang and today > self.due_date_gudang:
                self.status = 'OVERDUE'
            elif self.due_date_gudang and today >= (self.due_date_gudang - timedelta(days=7)):
                self.status = 'WARNING'
            else:
                self.status = 'AMAN'
                
        # Simpan Data SO Dulu (agar dapat ID)
        super().save(*args, **kwargs)

        # --- [FIX BARU] CATAT KE KARTU STOK (LOGIC INBOUND) ---
        # Hanya jalankan jika ini adalah input baru (Penebusan Baru)
        if is_new:
            # Kita panggil model StockCard secara dinamis agar tidak circular import
            StockCard = apps.get_model('warehouse', 'StockCard')
            
            StockCard.objects.create(
                sales_order=self,
                date=timezone.now(),
                transaction_type='IN', # Tipe MASUK
                reference_number=f"SO/{self.so_code}", # Ref pakai Kode SO
                tonnage_in=self.initial_tonnage,
                tonnage_out=0,
                balance=self.current_stock,
                status_location='PENYANGGA',
                description=f"Penebusan Awal ({self.district_allocation})"
            )


class Distribution(models.Model):
    """
    OUTBOUND: Pencatatan Penyaluran ke Kios.
    """
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='distributions', verbose_name="Sumber SO")
    kios = models.ForeignKey(Kios, on_delete=models.CASCADE)
    armada = models.ForeignKey(Armada, on_delete=models.SET_NULL, null=True, blank=True)
    
    distribution_date = models.DateField(default=timezone.now, verbose_name="Tanggal Kirim")
    tonnage_sent = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tonase Dikirim")
    
    do_number = models.CharField(max_length=50, blank=True, verbose_name="No. Surat Jalan (Auto)")
    notes = models.TextField(blank=True, verbose_name="Keterangan")

    def clean(self):
        # Validasi: Tidak boleh kirim lebih dari sisa stok!
        if self.pk is None: 
            if self.tonnage_sent > self.sales_order.current_stock:
                raise ValidationError(f"Stok tidak cukup! Sisa SO ini hanya: {self.sales_order.current_stock} Ton")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # 1. Generate No Surat Jalan
        if not self.do_number:
            super().save(*args, **kwargs) 
            self.do_number = f"SJ/{self.distribution_date.strftime('%Y%m%d')}/{self.id:04d}"
            super().save(update_fields=['do_number'])
        else:
            super().save(*args, **kwargs)

        # 2. Logic Data Baru (Potong Stok & Auto Invoice)
        if is_new:
            # A. Potong Stok SO
            self.sales_order.current_stock -= self.tonnage_sent
            self.sales_order.save()
            
            # B. Catat Kartu Stok
            StockCard.objects.create(
                sales_order=self.sales_order,
                date=timezone.now(),
                transaction_type='OUT',
                reference_number=self.do_number,
                tonnage_in=0,
                tonnage_out=self.tonnage_sent,
                balance=self.sales_order.current_stock,
                description=f"Kirim ke {self.kios.name}",
                status_location='PENYANGGA' # Default keluar dari penyangga
            )

            # C. Auto-Create Invoice di Finance
            Invoice = apps.get_model('finance', 'Invoice')
            if not hasattr(self, 'invoice'):
                Invoice.objects.create(
                    distribution=self,
                    created_at=self.distribution_date,
                    # Field lain dihitung otomatis oleh Invoice.save()
                )

    def __str__(self):
        return f"{self.do_number} -> {self.kios.name}"
        
    class Meta:
        verbose_name = "Penyaluran"
        verbose_name_plural = "Data Penyaluran"


class StockCard(models.Model):
    """
    LOG: Riwayat keluar masuk barang per SO
    """
    LOC_CHOICES = [('PENYANGGA', 'Gudang Penyangga'), ('KANTOR', 'Gudang Kantor')] # [BARU]
    
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=[('IN', 'Masuk'), ('OUT', 'Keluar')])
    reference_number = models.CharField(max_length=50, verbose_name="No Ref")
    
    tonnage_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tonnage_out = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Saldo Akhir")
    
    # [BARU] Field yang menyebabkan error tadi
    status_location = models.CharField(max_length=20, choices=LOC_CHOICES, default='PENYANGGA')
    
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.reference_number} - {self.transaction_type}"
    
    class Meta:
        ordering = ['-date']