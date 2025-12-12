from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib import messages # Import messages wajib ada
from xhtml2pdf import pisa
from django.db.models import Sum

from .models import Invoice, Payment
from .forms import PaymentForm

# --- FUNGSI BANTUAN CETAK PDF ---
def render_pdf_view(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="invoice.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response

# --- 1. CETAK INVOICE ---
class InvoicePDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Ambil invoice berdasarkan ID Distribution
        invoice = get_object_or_404(Invoice, distribution__id=pk) 
        
        context = {
            'inv': invoice,
            'company_name': 'CV SEMBADA TANI',
            'company_address': 'Jalan Raya Pupuk No. 1, Semarang',
        }
        return render_pdf_view('finance/pdf_invoice.html', context)

# --- 2. MONITORING PIUTANG (LIST) ---
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'finance/invoice_list.html'
    context_object_name = 'invoices'
    ordering = ['due_date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date() # Untuk cek telat bayar
        return context

# --- 3. INPUT PEMBAYARAN (FIX ERROR DISINI) ---
class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Ambil invoice dulu untuk memastikan ID valid
        self.invoice = get_object_or_404(Invoice, pk=kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # [FIX] Cek eksplisit: Jika instance None, buat Payment baru
        instance = kwargs.get('instance')
        if instance is None:
            instance = Payment()
        
        # Tempelkan invoice ke instance Payment SEBELUM validasi
        instance.invoice = self.invoice
        kwargs['instance'] = instance
        return kwargs

    def form_valid(self, form):
        # Pastikan user pencatat tersimpan
        form.instance.recorded_by = self.request.user
        form.instance.invoice = self.invoice # Double check
        form.save()
        messages.success(self.request, "Pembayaran berhasil dicatat!")
        return redirect('invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = self.invoice
        return context