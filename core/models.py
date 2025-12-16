from django.db import models
from django.contrib.auth.models import AbstractUser

# --- 1. MASTER WILAYAH (KABUPATEN) ---
class Regency(models.Model):
    """Tabel Kabupaten (Semarang, Klaten, dll)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nama Kabupaten")
    code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Kode Area")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Master Kabupaten"


# --- 2. CUSTOM USER (LOGIN) ---
class User(AbstractUser):
    """Custom User dengan Role & Wilayah"""
    ROLE_CHOICES = [
        ('SUPERUSER', 'Super Admin (Owner)'),
        ('ADMIN_GUDANG', 'Admin Gudang'),     # Saya sesuaikan dengan kode views sebelumnya
        ('ADMIN_FINANCE', 'Admin Keuangan'),  # Saya sesuaikan dengan kode views sebelumnya
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ADMIN_GUDANG')
    
    # Jika Admin, dia pegang wilayah mana? (Kalau Superuser, ini kosong/Null)
    assigned_regency = models.ForeignKey(
        Regency, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Khusus untuk Admin Gudang. Kosongkan untuk Superuser."
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# --- 3. MASTER KIOS ---
class Kios(models.Model):
    regency = models.ForeignKey(Regency, on_delete=models.CASCADE, related_name='kios_list')
    name = models.CharField(max_length=100, verbose_name="Nama Kios")
    pic_name = models.CharField(max_length=100, verbose_name="Nama Penanggung Jawab")
    address = models.TextField(verbose_name="Alamat Lengkap")
    phone = models.CharField(max_length=20, verbose_name="Nomor HP")
    district = models.CharField(max_length=100, verbose_name="Kecamatan") 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.district})"
    
    class Meta:
        verbose_name_plural = "Master Kios"


# --- 4. ALOKASI PEMERINTAH (PER KIOS) ---
class KiosAllocation(models.Model):
    PUPUK_CHOICES = [('UREA', 'UREA'), ('NPK', 'NPK')]
    
    kios = models.ForeignKey(Kios, on_delete=models.CASCADE, related_name='allocations')
    year = models.IntegerField(default=2025, verbose_name="Tahun Anggaran")
    fertilizer_type = models.CharField(max_length=10, choices=PUPUK_CHOICES)
    
    allocation_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Jatah Alokasi (Ton)")
    
    # Field ini opsional (bisa dihitung real-time), tapi kita simpan untuk cache/history
    realization_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Sudah Disalurkan (Ton)")

    class Meta:
        unique_together = ['kios', 'fertilizer_type', 'year'] # Mencegah duplikasi kuota di tahun yg sama
        verbose_name = "Alokasi RDKK"
        verbose_name_plural = "Master Alokasi RDKK"

    def __str__(self):
        return f"{self.kios.name} - {self.fertilizer_type} ({self.year})"


# --- 5. MASTER ARMADA ---
class Armada(models.Model):
    regency = models.ForeignKey(Regency, on_delete=models.CASCADE)
    plate_number = models.CharField(max_length=20, unique=True, verbose_name="Plat Nomor")
    vehicle_type = models.CharField(max_length=50, verbose_name="Jenis Kendaraan (Truk/PickUp)")
    driver_name = models.CharField(max_length=100, verbose_name="Nama Supir", blank=True)

    def __str__(self):
        return f"{self.plate_number} - {self.driver_name}"
    
    class Meta:
        verbose_name_plural = "Master Armada"


# --- 6. MASTER HARGA ---
class FertilizerPrice(models.Model):
    # Menggunakan char field untuk tipe pupuk agar fleksibel tapi unik
    fertilizer_type = models.CharField(max_length=10, unique=True, verbose_name="Jenis Pupuk") 
    price_per_ton = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Harga Per Ton (Rp)")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fertilizer_type}: Rp {self.price_per_ton:,.0f}"
    
    class Meta:
        verbose_name_plural = "Master Harga Pupuk"