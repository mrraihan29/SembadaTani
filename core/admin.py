from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Regency, Kios, Armada, FertilizerPrice, KiosAllocation

# --- 1. USER ADMIN (Bawaan Django disesuaikan) ---
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'assigned_regency', 'is_staff')
    list_filter = ('role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Info', {'fields': ('role', 'assigned_regency')}),
    )

# --- 2. MASTER WILAYAH ---
@admin.register(Regency)
class RegencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)

# --- 3. MASTER KIOS ---
@admin.register(Kios)
class KiosAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'pic_name', 'phone')
    list_filter = ('district',)
    search_fields = ('name', 'district')

# --- 4. MASTER ALOKASI RDKK (INI YANG TADI HILANG) ---
@admin.register(KiosAllocation)
class KiosAllocationAdmin(admin.ModelAdmin):
    list_display = ('kios', 'year', 'fertilizer_type', 'allocation_amount')
    list_filter = ('year', 'fertilizer_type')
    search_fields = ('kios__name',)
    ordering = ['kios__district']

# --- 5. MASTER ARMADA ---
@admin.register(Armada)
class ArmadaAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'driver_name', 'vehicle_type', 'regency')

# --- 6. MASTER HARGA ---
@admin.register(FertilizerPrice)
class FertilizerPriceAdmin(admin.ModelAdmin):
    list_display = ('fertilizer_type', 'price_per_ton', 'updated_at')