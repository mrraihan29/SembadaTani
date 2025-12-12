from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Regency, Kios, KiosAllocation, Armada, FertilizerPrice

# 1. Custom User Admin (Agar field 'role' & 'regency' muncul)
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Info Tambahan', {'fields': ('role', 'assigned_regency')}),
    )
    list_display = ('username', 'email', 'role', 'assigned_regency', 'is_active')
    list_filter = ('role', 'assigned_regency', 'is_active')

# 2. Master Wilayah
@admin.register(Regency)
class RegencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)

# 3. Master Kios & Alokasi (Inline)
class AllocationInline(admin.TabularInline):
    model = KiosAllocation
    extra = 1  # Menampilkan 1 baris kosong untuk input

@admin.register(Kios)
class KiosAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'regency', 'pic_name', 'phone')
    list_filter = ('regency', 'district')
    search_fields = ('name', 'pic_name')
    inlines = [AllocationInline] # Agar bisa input alokasi langsung di halaman Kios

# 4. Master Armada
@admin.register(Armada)
class ArmadaAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'vehicle_type', 'driver_name', 'regency')
    list_filter = ('regency', 'vehicle_type')

# 5. Master Harga
@admin.register(FertilizerPrice)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('fertilizer_type', 'price_per_ton', 'updated_at')