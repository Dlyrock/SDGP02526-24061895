from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # LANDING
    path('', views.landing, name='landing'),

    # REGISTER
    path('register/', views.register, name='register'),

    # LOGIN
    path('login/', views.tenant_login, name='login'),
    path('login/tenant/', views.tenant_login, name='tenant_login'),
    path('login/admin/', views.admin_login, name='admin_login'),

    # LOGOUT
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # DASHBOARD
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # TENANT FORMS
    path('dashboard/tenant/payment/', views.payment_form, name='payment_form'),
    path('dashboard/tenant/maintenance/', views.maintenance_request, name='maintenance_request'),
    path('dashboard/tenant/complaint/', views.complaint_form, name='complaint_form'),
]