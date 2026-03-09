from django import forms
from .models import Tenant, Complaint, MaintenanceRequest, Payment

# ----------------------
# TENANT FORM
# ----------------------
class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'ni_number']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'})
        }


# ----------------------
# COMPLAINT FORM
# ----------------------
class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['apartment', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4})
        }


# ----------------------
# MAINTENANCE REQUEST FORM
# ----------------------
class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['apartment', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4})
        }


# ----------------------
# PAYMENT FORM (Simulation)
# ----------------------
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['lease', 'amount', 'due_date', 'paid_date', 'method']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_date': forms.DateInput(attrs={'type': 'date'}),
        }
