from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .decorators import role_required
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import User
from .forms import UserForm

# Import Model dari Apps lain
from warehouse.models import SalesOrder
from finance.models import Invoice

@login_required
def dashboard_view(request):
    today = timezone.now().date()
    warning_threshold = today + timezone.timedelta(days=7)

    # --- 1. KPI STOK GUDANG ---
    # Hitung total sisa stok dari semua SO yang aktif
    total_stock_data = SalesOrder.objects.aggregate(total=Sum('current_stock'))
    total_stock = total_stock_data['total'] or 0

    # --- 2. KPI KEUANGAN (PIUTANG) ---
    # Hitung (Total Tagihan - Sudah Dibayar) hanya untuk invoice yang belum lunas
    piutang_data = Invoice.objects.filter(
        status__in=['UNPAID', 'PARTIAL']
    ).aggregate(
        sisa_hutang=Sum(F('total_amount') - F('amount_paid'))
    )
    total_piutang = piutang_data['sisa_hutang'] or 0

    # --- 3. KPI WARNING SYSTEM (Jatuh Tempo) ---
    # Stok yang sudah lewat jatuh tempo DAN masih ada sisa barangnya
    overdue_sos = SalesOrder.objects.filter(
        due_date_gudang__lt=today, 
        current_stock__gt=0
    )
    
    # Stok yang akan jatuh tempo dalam 7 hari ke depan DAN masih ada sisa
    warning_sos = SalesOrder.objects.filter(
        due_date_gudang__range=[today, warning_threshold],
        current_stock__gt=0
    )

    count_overdue = overdue_sos.count()
    count_warning = warning_sos.count()

    context = {
        'today': today,
        'total_stock': total_stock,
        'total_piutang': total_piutang,
        'count_overdue': count_overdue,
        'count_warning': count_warning,
        # Kirim list detail agar bisa ditampilkan di tabel mini dashboard
        'warning_list': warning_sos | overdue_sos, 
    }

    return render(request, 'dashboard.html', context)

# --- MANAJEMEN USER (KHUSUS SUPERUSER) ---
@method_decorator(role_required(allowed_roles=['SUPERUSER']), name='dispatch')
class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'core/user_list.html'
    context_object_name = 'users'

@method_decorator(role_required(allowed_roles=['SUPERUSER']), name='dispatch')
class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        messages.success(self.request, "User baru berhasil dibuat!")
        return super().form_valid(form)

@method_decorator(role_required(allowed_roles=['SUPERUSER']), name='dispatch')
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        messages.success(self.request, "Data user berhasil diperbarui!")
        return super().form_valid(form)

@method_decorator(role_required(allowed_roles=['SUPERUSER']), name='dispatch')
class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'core/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')