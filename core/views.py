import json
from django.shortcuts import render
from django.db.models import F
from .models import Tenant, Apartment, Payment, MaintenanceRequest, Complaint
from datetime import date

def dashboard(request):
    tenants = Tenant.objects.all()
    apartments = Apartment.objects.all()
    available_apartments = apartments.filter(available=True)
    occupied_apartments = apartments.filter(available=False)
    recent_requests = MaintenanceRequest.objects.order_by('-date_requested')[:5]
    recent_complaints = Complaint.objects.order_by('-date')[:5]

    # Tenant payments JSON 
    tenant_payments_list = []
    for tenant in tenants:
        payments = Payment.objects.filter(tenant=tenant).order_by('due_date')
        tenant_payments_list.append({
            'tenant_id': tenant.id,
            'tenant_name': f"{tenant.first_name} {tenant.last_name}",
            'dates': [p.due_date.strftime("%Y-%m-%d") for p in payments],
            'amounts': [float(p.amount) for p in payments],
        })

    # Tenant vs Neighbors (same apartment)
    tenant_vs_neighbors = []
    for tenant in tenants:
        lease = getattr(tenant, 'lease', None)  # Tenant'ın aktif lease'i
        if lease is None:
            continue
        apartment = lease.apartment
        neighbors_qs = Tenant.objects.filter(lease__apartment=apartment).exclude(id=tenant.id)
        tenant_vs_neighbors.append({
            'tenant_name': f"{tenant.first_name} {tenant.last_name}",
            'apartment': apartment.address,
            'neighbors': [
                {
                    'name': f"{n.first_name} {n.last_name}",
                    'payments': [float(p.amount) for p in Payment.objects.filter(tenant=n).order_by('due_date')]
                } for n in neighbors_qs
            ]
        })

    # Late payments per apartment
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
        'tenant_vs_neighbors_json': json.dumps(tenant_vs_neighbors),
        'late_payments_json': json.dumps(late_payments),
        'maintenance_summary': {
            'pending': MaintenanceRequest.objects.filter(status='pending').count(),
            'in_progress': MaintenanceRequest.objects.filter(status='in_progress').count(),
            'completed': MaintenanceRequest.objects.filter(status='completed').count(),
        }
    }
    return render(request, 'core/dashboard.html', context)