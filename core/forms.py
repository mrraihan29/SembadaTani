from django import forms
from .models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False, help_text="Kosongkan jika tidak ingin mengubah password.")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'assigned_regency', 'password', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'assigned_regency': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'role': 'Jabatan / Role',
            'assigned_regency': 'Wilayah Tugas (Khusus Admin Gudang)',
            'is_active': 'Status Aktif (Bisa Login?)'
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Logic khusus untuk encrypt password
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user