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
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),

    # DASHBOARD
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/tenant/', views.tenant_dashboard, name='tenant_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # TENANT ACTIONS
    path('payment/', views.payment_form, name='payment_form'),
    path('maintenance/', views.maintenance_request, name='maintenance_request'),
    path('complaint/', views.complaint_form, name='complaint_form'),
    path('lease/terminate/', views.request_early_termination, name='request_early_termination'),

    # STAFF PANEL
    path('staff/', views.staff_panel, name='staff_panel'),

    # MAINTENANCE MANAGEMENT (staff)
    path('staff/maintenance/<int:pk>/update/', views.update_maintenance, name='update_maintenance'),

    # COMPLAINT MANAGEMENT (staff)
    path('staff/complaint/<int:pk>/resolve/', views.resolve_complaint, name='resolve_complaint'),
    path('staff/complaint/<int:pk>/delete/', views.delete_complaint, name='delete_complaint'),

    # FRONTDESK
    path('frontdesk/', views.frontdesk_panel, name='frontdesk_panel'),
    path('frontdesk/tenant/add/', views.frontdesk_add_tenant, name='frontdesk_add_tenant'),

    # FINANCE
    path('finance/', views.finance_panel, name='finance_panel'),

    # MANAGER
    path('manager/', views.manager_panel, name='manager_panel'),
    path('manager/city/add/', views.manager_add_city, name='manager_add_city'),
]