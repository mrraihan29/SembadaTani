from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_date', 'amount', 'method', 'proof_image', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'amount': 'Jumlah Bayar (Rp)',
            'proof_image': 'Bukti Transfer (Struk)',
        }