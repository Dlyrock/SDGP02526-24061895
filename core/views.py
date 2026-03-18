import json
from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.db.models import F
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from .forms import (
    CustomUserCreationForm,
    MaintenanceRequestForm,
    ComplaintForm,
    PaymentForm,
)
from .models import (
    User,
    Tenant,
    Apartment,
    Payment,
    MaintenanceRequest,
    Complaint,
    Lease
)


def landing(request):
    return render(request, 'landing.html')


def register(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'role', None) == 'TENANT':
            return redirect('tenant_dashboard')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('tenant_dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'tenant/register.html', {'form': form})


def tenant_login(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'role', None) == 'TENANT':
            return redirect('tenant_dashboard')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if getattr(user, 'role', None) == 'TENANT':
                login(request, user)
                return redirect('tenant_dashboard')
            else:
                form.add_error(None, 'This is not a tenant account.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def admin_login(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'role', None) == 'TENANT':
            return redirect('tenant_dashboard')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if getattr(user, 'role', None) in ['ADMIN', 'MANAGER', 'FRONTDESK', 'FINANCE', 'MAINTENANCE']:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                form.add_error(None, 'This is not an admin account.')
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def dashboard_redirect(request):
    if request.user.role == 'TENANT':
        return redirect('tenant_dashboard')
    return redirect('admin_dashboard')


@login_required
def tenant_dashboard(request):
    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.warning(request, "No tenant profile is linked to this account yet.")
        return render(request, 'tenant/dashboard.html')

    lease = Lease.objects.filter(tenant=tenant).first()
    apartment = lease.apartment if lease else None

    payments = Payment.objects.filter(tenant=tenant).order_by('due_date')
    maintenance_items = MaintenanceRequest.objects.filter(tenant=tenant).order_by('-date_requested')
    complaints = Complaint.objects.filter(tenant=tenant)

    late_invoices = [p for p in payments if p.is_late]

    maintenance_open_count = maintenance_items.exclude(status='completed').count()
    complaint_open_count = complaints.exclude(status='resolved').exclude(status='closed').count()

    payment_history_labels = [p.due_date.strftime("%b %Y") for p in payments]
    payment_history_amounts = [float(p.amount) for p in payments]

    neighbors_labels = ["You"]
    neighbors_amounts = [sum(payment_history_amounts)]

    if apartment:
        neighbor_tenants = Tenant.objects.filter(
            lease__apartment=apartment
        ).exclude(id=tenant.id)

        for n in neighbor_tenants:
            n_payments = Payment.objects.filter(tenant=n)
            neighbors_labels.append(n.first_name)
            neighbors_amounts.append(sum([float(p.amount) for p in n_payments]))

    context = {
        "tenant": {
            "apartment_code": apartment.address if apartment else None,
            "city": apartment.city.name if apartment else None
        },
        "late_invoices": late_invoices,
        "maintenance_open_count": maintenance_open_count,
        "complaint_open_count": complaint_open_count,
        "maintenance_items": maintenance_items,
        "payment_history_labels": payment_history_labels,
        "payment_history_amounts": payment_history_amounts,
        "neighbors_labels": neighbors_labels,
        "neighbors_amounts": neighbors_amounts,
    }

    return render(request, "tenant/dashboard.html", context)


@login_required
def admin_dashboard(request):
    tenants = Tenant.objects.all()
    apartments = Apartment.objects.all()

    available_apartments = apartments.filter(available=True)
    occupied_apartments = apartments.filter(available=False)

    recent_requests = MaintenanceRequest.objects.order_by('-date_requested')[:5]
    recent_complaints = Complaint.objects.order_by('-date')[:5]

    tenant_payments_list = []

    for tenant in tenants:
        payments = Payment.objects.filter(tenant=tenant).order_by('due_date')

        tenant_payments_list.append({
            'tenant_id': tenant.id,
            'tenant_name': f"{tenant.first_name} {tenant.last_name}",
            'dates': [p.due_date.strftime("%Y-%m-%d") for p in payments],
            'amounts': [float(p.amount) for p in payments],
        })

    late_payments = {}

    for apt in apartments:
        late_count = Payment.objects.filter(
            lease__apartment=apt,
            paid_date__gt=F('due_date')
        ).count() + Payment.objects.filter(
            lease__apartment=apt,
            paid_date__isnull=True,
            due_date__lt=date.today()
        ).count()

        late_payments[apt.address] = late_count

    context = {
        'tenants': tenants,
        'available_apartments': available_apartments,
        'occupied_apartments': occupied_apartments,
        'recent_requests': recent_requests,
        'recent_complaints': recent_complaints,
        'tenant_payments_json': json.dumps(tenant_payments_list),
        'late_payments_json': json.dumps(late_payments),
        'maintenance_summary': {
            'pending': MaintenanceRequest.objects.filter(status='pending').count(),
            'in_progress': MaintenanceRequest.objects.filter(status='in_progress').count(),
            'completed': MaintenanceRequest.objects.filter(status='completed').count(),
        }
    }

    return render(request, 'admin/dashboard.html', context)


@login_required
def payment_form(request):
    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile is linked to this account.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()

    # Eğer lease yoksa demo amaçlı otomatik oluştur
    if not lease:
        apartment = Apartment.objects.filter(available=True).first() or Apartment.objects.first()

        if not apartment:
            messages.error(request, "No apartment exists in the system yet.")
            return redirect('tenant_dashboard')

        lease = Lease.objects.create(
            tenant=tenant,
            apartment=apartment,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            rent_amount=apartment.rent,
            deposit=0
        )

        apartment.available = False
        apartment.save()

    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            Payment.objects.create(
                tenant=tenant,
                lease=lease,
                amount=form.cleaned_data['amount'],
                due_date=date.today(),
                paid_date=date.today(),
                method=form.cleaned_data['payment_method']
            )
            messages.success(request, "Payment recorded successfully.")
            return redirect('tenant_dashboard')
    else:
        form = PaymentForm()

    return render(request, 'tenant/payment_form.html', {'form': form})


@login_required
def maintenance_request(request):
    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile is linked to this account.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()
    apartment = lease.apartment if lease else (Apartment.objects.first())

    if not apartment:
        messages.error(request, "No apartment exists in the system yet.")
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)

        if form.is_valid():
            mr = form.save(commit=False)
            mr.tenant = tenant
            mr.apartment = apartment
            mr.save()
            messages.success(request, "Maintenance request submitted successfully.")
            return redirect('tenant_dashboard')
    else:
        form = MaintenanceRequestForm()

    return render(request, 'tenant/maintenance_request_form.html', {'form': form})


@login_required
def complaint_form(request):
    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile is linked to this account.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()
    apartment = lease.apartment if lease else (Apartment.objects.first())

    if not apartment:
        messages.error(request, "No apartment exists in the system yet.")
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        form = ComplaintForm(request.POST)

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = tenant
            complaint.apartment = apartment
            complaint.save()
            messages.success(request, "Complaint submitted successfully.")
            return redirect('tenant_dashboard')
    else:
        form = ComplaintForm()

    return render(request, 'tenant/complaint_form.html', {'form': form})