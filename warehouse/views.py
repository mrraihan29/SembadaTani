from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction # Untuk integritas dan atomicity data

from .models import SalesOrder, Distribution, StockCard
from .forms import SalesOrderForm, DistributionForm

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from django.db.models import Sum, F
from django.db.models.functions import Coalesce # Untuk mengembalikan nilai pertama yang non-NULL
from core.models import Kios, KiosAllocation

from django.utils.decorators import method_decorator
from core.decorators import role_required

# --- 1. LIST STOK (GUDANG) ---
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class SalesOrderListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'warehouse/so_list.html'
    context_object_name = 'orders'
    ordering = ['due_date_gudang']

    def get_queryset(self):
        # Filter: Hanya tampilkan SO yang masih OPEN (ada stok) atau WARNING
        return SalesOrder.objects.filter(status__in=['AMAN', 'WARNING', 'OVERDUE'])

# --- 2. INPUT PENEBUSAN (STOCK IN) ---
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class PenebusanCreateView(LoginRequiredMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'warehouse/penebusan_form.html'
    success_url = reverse_lazy('so_list') # Setelah simpan, balik ke list

    def form_valid(self, form):
        messages.success(self.request, "Data Penebusan (SO) Berhasil Disimpan!")
        return super().form_valid(form)
    
# --- 3. LIST PENYALURAN (DISTRIBUSI) ---
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class DistributionListView(LoginRequiredMixin, ListView):
    model = Distribution
    template_name = 'warehouse/dist_list.html'
    context_object_name = 'distributions'
    ordering = ['-distribution_date']

# --- 4. INPUT PENYALURAN (STOCK OUT) ---
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class PenyaluranCreateView(LoginRequiredMixin, CreateView):
    model = Distribution
    form_class = DistributionForm
    template_name = 'warehouse/penyaluran_form.html'
    success_url = reverse_lazy('dist_list')

    def form_valid(self, form):
        try:
            # Gunakan atomic transaction: Jika gagal bikin Invoice, batalkan semua (termasuk potong stok)
            with transaction.atomic():
                self.object = form.save()
            messages.success(self.request, f"Penyaluran Berhasil! Surat Jalan: {self.object.do_number}")
            return redirect(self.success_url)
        except Exception as e:
            form.add_error(None, f"Terjadi Kesalahan: {e}")
            return self.form_invalid(form)
        
# --- FUNGSI BANTUAN CETAK PDF ---
def render_pdf_view(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    # Jika ingin langsung download, ubah 'inline' jadi 'attachment'
    response['Content-Disposition'] = 'inline; filename="document.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

# --- 5. CETAK SURAT JALAN ---
from django.views import View
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class SuratJalanPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        dist = Distribution.objects.get(pk=pk)
        context = {
            'dist': dist,
            'today': timezone.now(),
        }
        return render_pdf_view('warehouse/pdf_surat_jalan.html', context)
    
# --- 6. LAPORAN KARTU STOK (HISTORY) ---
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class StockCardListView(LoginRequiredMixin, ListView):
    model = StockCard
    template_name = 'warehouse/stock_card_list.html'
    context_object_name = 'cards'
    paginate_by = 50 # Tampilkan 50 baris per halaman
    ordering = ['-date']

    def get_queryset(self):
        # Ambil semua data & optimasi query (join ke sales_order)
        queryset = StockCard.objects.all().select_related('sales_order')
        
        # --- FITUR FILTER ---
        # 1. Filter by Kode SO (Pencarian Teks)
        so_code = self.request.GET.get('so_code')
        if so_code:
            queryset = queryset.filter(sales_order__so_code__icontains=so_code)
            
        # 2. Filter by Jenis Transaksi (IN/OUT)
        trans_type = self.request.GET.get('type')
        if trans_type:
            queryset = queryset.filter(transaction_type=trans_type)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Kirim data tambahan jika ingin buat dropdown SO (Optional)
        # Kita pakai text input dulu biar ringan
        return context
    
# --- 7. MONITORING REALISASI ALOKASI ---
@method_decorator(role_required(allowed_roles=['ADMIN_GUDANG']), name='dispatch')
class AllocationReportView(LoginRequiredMixin, ListView):
    template_name = 'warehouse/allocation_report.html'
    context_object_name = 'report_data'
    
    def get_queryset(self):
        self.selected_type = self.request.GET.get('type', 'UREA')
        
        data_report = []
        all_kios = Kios.objects.all().order_by('district', 'name')
        
        for kios in all_kios:
            # 1. Ambil Jatah (Allocation)
            try:
                alloc = KiosAllocation.objects.get(
                    kios=kios, 
                    fertilizer_type=self.selected_type,
                    year=2025
                )
                # [FIX DISINI] Gunakan allocation_amount sesuai models.py
                quota = alloc.allocation_amount 
            except KiosAllocation.DoesNotExist:
                quota = 0
            
            # 2. Hitung Realisasi
            realization = Distribution.objects.filter(
                kios=kios,
                sales_order__fertilizer_type=self.selected_type
            ).aggregate(total=Sum('tonnage_sent'))['total'] or 0
            
            # 3. Hitung Sisa & Persen
            remaining = quota - realization
            percentage = (realization / quota * 100) if quota > 0 else 0
            
            if quota > 0 or realization > 0:
                data_report.append({
                    'kios': kios,
                    'quota': quota,
                    'realization': realization,
                    'remaining': remaining,
                    'percentage': percentage,
                    'status': 'OVER' if remaining < 0 else 'AMAN'
                })
                
        return data_report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_type'] = self.selected_type
        return context