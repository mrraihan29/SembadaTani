from django.contrib import admin
from .models import Invoice, Payment

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('recorded_by',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'get_kios', 'created_at', 'total_amount', 'amount_paid', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('invoice_number', 'distribution__kios__name')
    inlines = [PaymentInline] # Bisa lihat history bayar di dalam invoice

    def get_kios(self, obj):
        return obj.distribution.kios.name
    get_kios.short_description = 'Kios'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'payment_date', 'amount', 'method', 'recorded_by')
    list_filter = ('method', 'payment_date')