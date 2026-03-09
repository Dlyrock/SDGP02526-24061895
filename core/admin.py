from django.contrib import admin
from .models import City, Apartment, Tenant, Lease, Payment, MaintenanceRequest, Complaint

admin.site.register(City)
admin.site.register(Apartment)
admin.site.register(Tenant)
admin.site.register(Lease)
admin.site.register(Payment)
admin.site.register(MaintenanceRequest)
admin.site.register(Complaint)
