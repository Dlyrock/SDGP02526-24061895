from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# ----------------------
# CUSTOM USER (ROLE SYSTEM)
# ----------------------

class User(AbstractUser):
    ROLE_CHOICES = [
        ('TENANT', 'Tenant'),
        ('FRONTDESK', 'Front Desk'),
        ('FINANCE', 'Finance Manager'),
        ('MAINTENANCE', 'Maintenance Staff'),
        ('ADMIN', 'Administrator'),
        ('MANAGER', 'Manager'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# ----------------------
# CORE MODELS
# ----------------------

class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='UK')
    zipcode = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name


class Apartment(models.Model):
    address = models.CharField(max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    bedrooms = models.IntegerField()
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1)
    rent = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.address}, {self.city.name}"


class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    ni_number = models.CharField(max_length=20, blank=True)  # National Insurance

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Lease(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Lease for {self.tenant} - {self.apartment}"


class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)

    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    method = models.CharField(max_length=50, choices=METHOD_CHOICES)

    @property
    def is_late(self):
        if self.paid_date and self.paid_date > self.due_date:
            return True
        if not self.paid_date and timezone.now().date() > self.due_date:
            return True
        return False

    def __str__(self):
        return f"Payment of {self.amount} by {self.tenant}"


class MaintenanceRequest(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    description = models.TextField()
    date_requested = models.DateField(auto_now_add=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    resolved_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Maintenance Request by {self.tenant}"


class Complaint(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return f"Complaint by {self.tenant}"