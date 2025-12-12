from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction # Untuk keamanan data

from .models import SalesOrder, Distribution
from .forms import SalesOrderForm, DistributionForm

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# --- 1. LIST STOK (GUDANG) ---
class SalesOrderListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'warehouse/so_list.html'
    context_object_name = 'orders'
    ordering = ['due_date_gudang']

    def get_queryset(self):
        # Filter: Hanya tampilkan SO yang masih OPEN (ada stok) atau WARNING
        return SalesOrder.objects.filter(status__in=['AMAN', 'WARNING', 'OVERDUE'])

# --- 2. INPUT PENEBUSAN (STOCK IN) ---
class PenebusanCreateView(LoginRequiredMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'warehouse/penebusan_form.html'
    success_url = reverse_lazy('so_list') # Setelah simpan, balik ke list

    def form_valid(self, form):
        messages.success(self.request, "Data Penebusan (SO) Berhasil Disimpan!")
        return super().form_valid(form)
    
# --- 3. LIST PENYALURAN (DISTRIBUSI) ---
class DistributionListView(LoginRequiredMixin, ListView):
    model = Distribution
    template_name = 'warehouse/dist_list.html'
    context_object_name = 'distributions'
    ordering = ['-distribution_date']

# --- 4. INPUT PENYALURAN (STOCK OUT) ---
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
class SuratJalanPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        dist = Distribution.objects.get(pk=pk)
        context = {
            'dist': dist,
            'today': timezone.now(),
        }
        return render_pdf_view('warehouse/pdf_surat_jalan.html', context)