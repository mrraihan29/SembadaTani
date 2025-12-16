from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # 1. Harus Login dulu
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs) # Biarkan login_required handle ini nanti
            
            # 2. Cek Jabatan
            # Superuser (Owner) selalu boleh masuk kemana saja
            if request.user.role == 'SUPERUSER' or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 3. Cek apakah jabatan user ada di daftar yang diizinkan
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # 4. Jika tidak cocok, tolak!
            raise PermissionDenied("ANDA TIDAK MEMILIKI AKSES KE HALAMAN INI!")
            
        return _wrapped_view
    return decorator