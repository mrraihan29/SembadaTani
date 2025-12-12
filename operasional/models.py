from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import User, Regency, Armada

class OperationalCost(models.Model):
    """
    Pencatatan Biaya Operasional (Armada & Kantor).
    Memiliki workflow Approval: Input Admin -> Pending -> ACC Owner -> Approved.
    """
    CATEGORY_CHOICES = [
        ('ARMADA', 'Biaya Armada (BBM/Servis/Ban)'),
        ('KANTOR', 'Biaya Kantor (Listrik/ATK/Makan)'),
        ('LAINNYA', 'Lain-lain'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Menunggu ACC Owner'),
        ('APPROVED', 'Disetujui (Cair)'),
        ('REJECTED', 'Ditolak'),
    ]

    # Scope Wilayah (Biaya ini beban kabupaten mana?)
    regency = models.ForeignKey(Regency, on_delete=models.CASCADE, verbose_name="Beban Wilayah")
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Kategori Biaya")
    
    # Optional: Hanya diisi jika kategori = ARMADA
    armada = models.ForeignKey(Armada, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Plat Nomor (Jika Armada)")
    
    description = models.TextField(verbose_name="Keterangan Pengeluaran")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Nominal (Rp)")
    
    # Bukti Foto (Nota/Struk)
    proof_image = models.ImageField(upload_to='operational_proofs/', blank=True, null=True, verbose_name="Foto Bukti")
    
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Tanggal Input")
    
    # Workflow Approval
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='expenses_created', verbose_name="Diinput Oleh")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_approved', verbose_name="Di-ACC Oleh")

    def clean(self):
        # Validasi: Jika kategori ARMADA, wajib pilih mobilnya!
        if self.category == 'ARMADA' and not self.armada:
            raise ValidationError({'armada': 'Untuk kategori Biaya Armada, wajib memilih Plat Nomor kendaraan!'})

    def save(self, *args, **kwargs):
        # Otomatis set approved_by jika status berubah jadi APPROVED
        if self.status == 'APPROVED' and not self.approved_by:
            # Note: Kita tidak bisa ambil request.user di model save, 
            # jadi ini nanti di-handle di Admin/View. 
            pass 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_category_display()} - Rp {self.amount:,.0f} ({self.status})"

    class Meta:
        verbose_name = "Biaya Operasional"
        verbose_name_plural = "Data Biaya Operasional"
        ordering = ['-created_at']