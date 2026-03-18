import json
from datetime import date

from django.shortcuts import render, redirect
from django.db.models import F
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm

from .models import (
    User,
    Tenant,
    Apartment,
    Payment,
    MaintenanceRequest,
    Complaint,
    Lease
)

# ----------------------
# LANDING PAGE
# ----------------------
def landing(request):
    return render(request, 'landing.html')


# ----------------------
# REGISTER (NEW)
# ----------------------
def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.role = 'TENANT'
            user.is_active = True
            user.save()

            Tenant.objects.create(
                user=user,
                first_name=user.username,
                last_name=""
            )

            login(request, user)
            return redirect('tenant_dashboard')

    else:
        form = UserCreationForm()

    return render(request, 'tenant/register.html', {'form': form})


# ----------------------
# LOGIN VIEWS
# ----------------------
def tenant_login(request):

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if user.role == 'TENANT':
                login(request, user)
                return redirect('tenant_dashboard')
            else:
                form.add_error(None, 'This is not a tenant account.')

    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def admin_login(request):

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if user.role in ['ADMIN', 'MANAGER', 'FRONTDESK', 'FINANCE', 'MAINTENANCE']:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                form.add_error(None, 'This is not an admin account.')

    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


# ----------------------
# DASHBOARD REDIRECT
# ----------------------
@login_required
def dashboard_redirect(request):

    if request.user.role == 'TENANT':
        return redirect('tenant_dashboard')

    return redirect('admin_dashboard')


# ----------------------
# TENANT DASHBOARD
# ----------------------
@login_required
def tenant_dashboard(request):

    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        return render(request, 'tenant/dashboard.html')

    lease = Lease.objects.filter(tenant=tenant).first()
    apartment = lease.apartment if lease else None

    payments = Payment.objects.filter(tenant=tenant).order_by('due_date')
    maintenance_items = MaintenanceRequest.objects.filter(tenant=tenant).order_by('-date_requested')
    complaints = Complaint.objects.filter(tenant=tenant)

    late_invoices = [p for p in payments if p.is_late]

    maintenance_open_count = maintenance_items.exclude(status='completed').count()
    complaint_open_count = complaints.exclude(status='resolved').count()

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
            neighbors_amounts.append(
                sum([float(p.amount) for p in n_payments])
            )

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


# ----------------------
# ADMIN DASHBOARD
# ----------------------
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


# ----------------------
# TENANT FORMS
# ----------------------
@login_required
def payment_form(request):

    tenant = Tenant.objects.filter(user=request.user).first()

    if request.method == 'POST':

        amount = request.POST.get('amount')
        method = request.POST.get('payment_method')

        lease = Lease.objects.filter(tenant=tenant).first()

        if tenant and lease:
            Payment.objects.create(
                tenant=tenant,
                lease=lease,
                amount=amount,
                due_date=date.today(),
                paid_date=date.today(),
                method=method
            )

        return redirect('tenant_dashboard')

    return render(request, 'tenant/payment_form.html')


@login_required
def maintenance_request(request):

    from .forms import MaintenanceRequestForm

    tenant = Tenant.objects.filter(user=request.user).first()
    lease = Lease.objects.filter(tenant=tenant).first()

    if request.method == 'POST':

        form = MaintenanceRequestForm(request.POST)

        if form.is_valid():

            mr = form.save(commit=False)
            mr.tenant = tenant
            mr.apartment = lease.apartment if lease else None
            mr.save()

            return redirect('tenant_dashboard')

    else:
        form = MaintenanceRequestForm()

    return render(request, 'tenant/maintenance_request_form.html', {'form': form})


@login_required
def complaint_form(request):

    from .forms import ComplaintForm

    tenant = Tenant.objects.filter(user=request.user).first()
    lease = Lease.objects.filter(tenant=tenant).first()

    if request.method == 'POST':

        form = ComplaintForm(request.POST)

        if form.is_valid():

            complaint = form.save(commit=False)
            complaint.tenant = tenant
            complaint.apartment = lease.apartment if lease else None
            complaint.save()

            return redirect('tenant_dashboard')

    else:
        form = ComplaintForm()

    return render(request, 'tenant/complaint_form.html', {'form': form})