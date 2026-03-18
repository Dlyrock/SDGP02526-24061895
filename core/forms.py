from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Tenant, Complaint, MaintenanceRequest, Payment


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=15, required=True)
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    ni_number = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'date_of_birth',
            'ni_number',
            'password1',
            'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already used by another user.")

        if Tenant.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already used by another tenant.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = 'TENANT'
        user.is_active = True

        if commit:
            user.save()

            Tenant.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data['phone'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                ni_number=self.cleaned_data.get('ni_number', '')
            )

        return user


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'ni_number']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'})
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})
        }


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})
        }


class PaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'})
    )
    payment_method = forms.ChoiceField(
        choices=Payment.METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )