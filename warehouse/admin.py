from django.contrib import admin
from .models import SalesOrder, Distribution, StockCard

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('so_code', 'fertilizer_type', 'district_allocation', 'initial_tonnage', 'current_stock', 'due_date_gudang', 'status')
    list_filter = ('status', 'fertilizer_type', 'regency')
    search_fields = ('so_code', 'district_allocation')
    ordering = ('due_date_gudang',) # Urutkan dari yang mau jatuh tempo
    
    # Supaya admin tidak sembarangan edit stok manual (harus lewat sistem)
    # readonly_fields = ('current_stock', 'status') 
    # Note: Sementara saya komen dulu readonly-nya agar Mas Dida (Superuser) bisa edit jika ada kesalahan input awal.

@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    list_display = ('do_number', 'distribution_date', 'kios', 'sales_order', 'tonnage_sent')
    list_filter = ('distribution_date', 'armada')
    search_fields = ('do_number', 'kios__name')
    date_hierarchy = 'distribution_date' # Navigasi tanggal di atas

@admin.register(StockCard)
class StockCardAdmin(admin.ModelAdmin):
    list_display = ('date', 'reference_number', 'sales_order', 'transaction_type', 'tonnage_in', 'tonnage_out', 'balance')
    list_filter = ('transaction_type', 'date')
    
    # Kartu stok adalah LOG HISTORY. Sebaiknya tidak diedit manual.
    def has_add_permission(self, request):
        return False # Tidak ada tombol 'Add' manual
    
    def has_delete_permission(self, request, obj=None):
        return False # Tidak boleh hapus log sembarangan