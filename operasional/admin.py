from django.contrib import admin
from .models import OperationalCost

@admin.register(OperationalCost)
class OperationalAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'amount', 'created_at', 'status', 'approved_by')
    list_filter = ('status', 'category', 'regency')
    search_fields = ('description',)
    
    actions = ['approve_expenses', 'reject_expenses']

    # Fitur Bulk Action (Centang banyak -> Klik Approve)
    @admin.action(description='ACC / Setujui Biaya Terpilih')
    def approve_expenses(self, request, queryset):
        queryset.update(status='APPROVED', approved_by=request.user)
        self.message_user(request, "Biaya terpilih berhasil di-ACC.")

    @admin.action(description='Tolak Biaya Terpilih')
    def reject_expenses(self, request, queryset):
        queryset.update(status='REJECTED', approved_by=request.user)