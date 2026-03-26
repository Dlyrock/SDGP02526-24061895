import json
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import F, Sum, Count
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from .forms import (
    CustomUserCreationForm,
    TenantForm,
    MaintenanceRequestForm,
    ComplaintForm,
    PaymentForm,
    CityForm,
)
from .models import (
    User,
    City,
    Tenant,
    Apartment,
    Payment,
    MaintenanceRequest,
    Complaint,
    Lease
)


# -------------------
# LANDING
# -------------------
def landing(request):
    return render(request, 'landing.html')


# -------------------
# REGISTER
# -------------------
def register(request):
    if request.user.is_authenticated:
        if request.user.role == 'TENANT':
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


# -------------------
# TENANT LOGIN
# -------------------
def tenant_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'TENANT':
            return redirect('tenant_dashboard')
        return redirect('admin_dashboard')

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


# -------------------
# ADMIN LOGIN
# -------------------
def admin_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'TENANT':
            return redirect('tenant_dashboard')
        return redirect('admin_dashboard')

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


# -------------------
# DASHBOARD REDIRECT
# -------------------
@login_required
def dashboard_redirect(request):
    if request.user.role == 'TENANT':
        return redirect('tenant_dashboard')
    return redirect('admin_dashboard')


# -------------------
# TENANT DASHBOARD
# -------------------
@login_required
def tenant_dashboard(request):

    if request.user.role != 'TENANT':
        return redirect('admin_dashboard')

    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.warning(request, "No tenant profile is linked.")
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


# -------------------
# ADMIN DASHBOARD
# -------------------
@login_required
def admin_dashboard(request):

    if request.user.role == 'TENANT':
        return redirect('tenant_dashboard')

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

    # Build tenant vs neighbors data for admin charts (fixes JS bug)
    tenant_vs_neighbors_list = []
    for tenant in tenants:
        lease = Lease.objects.filter(tenant=tenant).first()
        apartment = lease.apartment if lease else None
        neighbor_data = []
        if apartment:
            neighbor_tenants = Tenant.objects.filter(
                lease__apartment=apartment
            ).exclude(id=tenant.id)
            for n in neighbor_tenants:
                n_payments = list(Payment.objects.filter(tenant=n).values_list('amount', flat=True))
                neighbor_data.append({
                    'name': n.first_name,
                    'payments': [float(p) for p in n_payments],
                })
        tenant_vs_neighbors_list.append({
            'tenant_name': f"{tenant.first_name} {tenant.last_name}",
            'neighbors': neighbor_data,
        })

    context = {
        'tenants': tenants,
        'available_apartments': available_apartments,
        'occupied_apartments': occupied_apartments,
        'recent_requests': recent_requests,
        'recent_complaints': recent_complaints,
        'tenant_payments_json': json.dumps(tenant_payments_list),
        'tenant_vs_neighbors_json': json.dumps(tenant_vs_neighbors_list),
        'late_payments_json': json.dumps(late_payments),
        'maintenance_summary': {
            'pending': MaintenanceRequest.objects.filter(status='pending').count(),
            'in_progress': MaintenanceRequest.objects.filter(status='in_progress').count(),
            'completed': MaintenanceRequest.objects.filter(status='completed').count(),
        }
    }

    return render(request, 'admin/dashboard.html', context)


# -------------------
# PAYMENT
# -------------------
@login_required
def payment_form(request):

    if request.user.role != 'TENANT':
        return redirect('admin_dashboard')

    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()


    if not lease:
        messages.error(request, "You do not have an active lease. Please contact the front desk.")
        return redirect("tenant_dashboard")


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
            messages.success(request, "Payment successful.")
            return redirect('tenant_dashboard')
    else:
        form = PaymentForm()

    return render(request, 'tenant/payment_form.html', {'form': form, 'lease': lease})


# -------------------
# MAINTENANCE
# -------------------
@login_required
def maintenance_request(request):

    if request.user.role != 'TENANT':
        return redirect('admin_dashboard')

    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()
    apartment = lease.apartment if lease else Apartment.objects.first()

    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            mr = form.save(commit=False)
            mr.tenant = tenant
            mr.apartment = apartment
            mr.save()
            messages.success(request, "Request submitted.")
            return redirect('tenant_dashboard')
    else:
        form = MaintenanceRequestForm()

    return render(request, 'tenant/maintenance_request_form.html', {'form': form})


# -------------------
# COMPLAINT
# -------------------
@login_required
def complaint_form(request):

    if request.user.role != 'TENANT':
        return redirect('admin_dashboard')

    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()
    apartment = lease.apartment if lease else Apartment.objects.first()

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = tenant
            complaint.apartment = apartment
            complaint.save()
            messages.success(request, "Complaint submitted.")
            return redirect('tenant_dashboard')
    else:
        form = ComplaintForm()

    return render(request, 'tenant/complaint_form.html', {'form': form})

# -------------------
# STAFF PANEL
# -------------------
@login_required
def staff_panel(request):
    if request.user.role not in ['ADMIN', 'MANAGER', 'FRONTDESK', 'FINANCE', 'MAINTENANCE']:
        return redirect('tenant_dashboard')

    maintenance_requests = MaintenanceRequest.objects.select_related('tenant', 'apartment').order_by('-date_requested')
    complaints = Complaint.objects.select_related('tenant', 'apartment').order_by('-date')

    return render(request, 'admin/staff_panel.html', {
        'maintenance_requests': maintenance_requests,
        'complaints': complaints,
    })


# -------------------
# UPDATE MAINTENANCE STATUS (staff)
# -------------------
@login_required
def update_maintenance(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER', 'MAINTENANCE', 'FRONTDESK']:
        return redirect('tenant_dashboard')

    mr = get_object_or_404(MaintenanceRequest, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        cost = request.POST.get('cost', 0)
        scheduled_date = request.POST.get('scheduled_date', None)
        time_taken = request.POST.get('time_taken', None)

        if new_status in ['pending', 'in_progress', 'completed']:
            mr.status = new_status

        if cost:
            try:
                mr.cost = Decimal(cost)
            except Exception:
                pass

        if scheduled_date:
            mr.scheduled_date = scheduled_date

        if time_taken:
            mr.time_taken = time_taken

        if new_status == 'completed':
            mr.resolved_date = date.today()

        mr.save()
        messages.success(request, f"Maintenance request updated to '{new_status}'.")

    return redirect('staff_panel')


# -------------------
# RESOLVE COMPLAINT (staff)
# -------------------
@login_required
def resolve_complaint(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER', 'FRONTDESK']:
        return redirect('tenant_dashboard')

    complaint = get_object_or_404(Complaint, pk=pk)
    complaint.status = 'resolved'
    complaint.save()
    messages.success(request, "Complaint marked as resolved.")
    return redirect('staff_panel')


# -------------------
# DELETE COMPLAINT (admin only)
# -------------------
@login_required
def delete_complaint(request, pk):
    if request.user.role not in ['ADMIN', 'MANAGER']:
        messages.error(request, "You don't have permission to delete complaints.")
        return redirect('staff_panel')

    complaint = get_object_or_404(Complaint, pk=pk)
    complaint.delete()
    messages.success(request, "Complaint deleted.")
    return redirect('staff_panel')


# -------------------
# FRONTDESK PANEL
# -------------------
@login_required
def frontdesk_panel(request):
    if request.user.role not in ['FRONTDESK', 'ADMIN', 'MANAGER']:
        return redirect('tenant_dashboard')

    query = request.GET.get('q', '')
    tenants = Tenant.objects.all()

    if query:
        tenants = tenants.filter(
            first_name__icontains=query
        ) | tenants.filter(
            last_name__icontains=query
        ) | tenants.filter(
            email__icontains=query
        ) | tenants.filter(
            ni_number__icontains=query
        )

    tenants = tenants.select_related('user').order_by('last_name')

    maintenance_requests = MaintenanceRequest.objects.select_related('tenant').order_by('-date_requested')[:10]
    complaints = Complaint.objects.select_related('tenant').order_by('-date')[:10]

    return render(request, 'admin/frontdesk_panel.html', {
        'tenants': tenants,
        'query': query,
        'maintenance_requests': maintenance_requests,
        'complaints': complaints,
    })


# -------------------
# FRONTDESK — ADD TENANT
# -------------------
@login_required
def frontdesk_add_tenant(request):
    if request.user.role not in ['FRONTDESK', 'ADMIN', 'MANAGER']:
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tenant registered successfully.")
            return redirect('frontdesk_panel')
    else:
        form = TenantForm()

    return render(request, 'admin/frontdesk_add_tenant.html', {'form': form})


# -------------------
# FINANCE PANEL
# -------------------
@login_required
def finance_panel(request):
    if request.user.role not in ['FINANCE', 'ADMIN', 'MANAGER']:
        return redirect('tenant_dashboard')

    # All payments
    all_payments = Payment.objects.select_related('tenant', 'lease__apartment').order_by('-due_date')

    # Late payments
    late_payments = [p for p in all_payments if p.is_late]

    # Financial summary
    total_collected = all_payments.filter(paid_date__isnull=False).aggregate(total=Sum('amount'))['total'] or 0
    total_pending = all_payments.filter(paid_date__isnull=True).aggregate(total=Sum('amount'))['total'] or 0

    # Per-apartment summary
    apartments = Apartment.objects.all()
    apt_summary = []
    for apt in apartments:
        collected = Payment.objects.filter(
            lease__apartment=apt, paid_date__isnull=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        pending = Payment.objects.filter(
            lease__apartment=apt, paid_date__isnull=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        apt_summary.append({
            'apartment': apt,
            'collected': collected,
            'pending': pending,
        })

    return render(request, 'admin/finance_panel.html', {
        'all_payments': all_payments[:50],
        'late_payments': late_payments,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'apt_summary': apt_summary,
    })


# -------------------
# MANAGER PANEL
# -------------------
@login_required
def manager_panel(request):
    if request.user.role not in ['MANAGER', 'ADMIN']:
        return redirect('tenant_dashboard')

    cities = City.objects.all()
    city_stats = []

    for city in cities:
        total_apts = Apartment.objects.filter(city=city).count()
        occupied = Apartment.objects.filter(city=city, available=False).count()
        available = Apartment.objects.filter(city=city, available=True).count()
        revenue = Payment.objects.filter(
            lease__apartment__city=city, paid_date__isnull=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        city_stats.append({
            'city': city,
            'total': total_apts,
            'occupied': occupied,
            'available': available,
            'revenue': revenue,
            'occupancy_rate': round((occupied / total_apts * 100), 1) if total_apts > 0 else 0,
        })

    return render(request, 'admin/manager_panel.html', {
        'city_stats': city_stats,
    })


# -------------------
# MANAGER — ADD CITY
# -------------------
@login_required
def manager_add_city(request):
    if request.user.role not in ['MANAGER', 'ADMIN']:
        return redirect('tenant_dashboard')

    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"City '{form.cleaned_data['name']}' added successfully.")
            return redirect('manager_panel')
    else:
        form = CityForm()

    return render(request, 'admin/manager_add_city.html', {'form': form})


# -------------------
# EARLY LEASE TERMINATION
# -------------------
@login_required
def request_early_termination(request):

    if request.user.role != 'TENANT':
        return redirect('admin_dashboard')

    tenant = Tenant.objects.filter(user=request.user).first()

    if not tenant:
        messages.error(request, "No tenant profile found.")
        return redirect('tenant_dashboard')

    lease = Lease.objects.filter(tenant=tenant).first()

    if not lease:
        messages.error(request, "You do not have an active lease.")
        return redirect('tenant_dashboard')

    if lease.early_termination_requested:
        messages.warning(request, "You have already submitted an early termination request.")
        return redirect('tenant_dashboard')

    # Calculate: notice period = today + 1 month, penalty = 5% of monthly rent
    today = date.today()
    # 1 month notice: add 30 days (safe cross-platform alternative)
    next_month = today.replace(day=1)
    if today.month == 12:
        notice_end_date = today.replace(year=today.year+1, month=1, day=today.day)
    else:
        import calendar
        last_day = calendar.monthrange(today.year, today.month+1)[1]
        notice_end_date = today.replace(month=today.month+1, day=min(today.day, last_day))
    penalty = lease.calculate_early_termination_penalty()

    if request.method == 'POST':
        lease.early_termination_requested = True
        lease.early_termination_date = notice_end_date
        lease.early_termination_penalty = penalty
        lease.save()
        messages.success(
            request,
            f"Early termination request submitted. "
            f"Your lease will end on {notice_end_date}. "
            f"Penalty charge: £{penalty}."
        )
        return redirect('tenant_dashboard')

    return render(request, 'tenant/early_termination.html', {
        'lease': lease,
        'notice_end_date': notice_end_date,
        'penalty': penalty,
    })
