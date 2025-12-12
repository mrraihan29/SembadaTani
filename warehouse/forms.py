from django import forms
from .models import SalesOrder, Distribution

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['so_code', 'regency', 'fertilizer_type', 'district_allocation', 'initial_tonnage', 'input_date']
        widgets = {
            'input_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        help_texts = {
            'so_code': 'Pastikan kode SO unik dan sesuai dokumen fisik.',
            'district_allocation': 'Kecamatan alokasi awal (bisa dipindah nanti).',
        }
        
class DistributionForm(forms.ModelForm):
    class Meta:
        model = Distribution
        fields = ['kios', 'sales_order', 'armada', 'tonnage_sent', 'distribution_date', 'notes']
        widgets = {
            'distribution_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'sales_order': 'Ambil Stok Dari (SO)',
            'tonnage_sent': 'Jumlah Kirim (Ton)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter: Hanya tampilkan SO yang stoknya > 0
        self.fields['sales_order'].queryset = SalesOrder.objects.filter(current_stock__gt=0).order_by('due_date_gudang')
        # Tampilkan info sisa stok di dropdown
        self.fields['sales_order'].label_from_instance = lambda obj: f"{obj.so_code} - Sisa: {obj.current_stock} Ton ({obj.district_allocation})"