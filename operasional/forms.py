from django import forms
from .models import OperationalCost

class OperationalForm(forms.ModelForm):
    class Meta:
        model = OperationalCost
        fields = ['regency', 'category', 'armada', 'description', 'amount', 'proof_image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
        help_texts = {
            'armada': 'Wajib diisi jika kategori adalah "Biaya Armada".',
            'proof_image': 'Upload foto nota/struk sebagai bukti.',
        }