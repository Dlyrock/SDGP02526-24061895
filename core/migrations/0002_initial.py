from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [

        # --- Lease: early termination fields ---
        migrations.AddField(
            model_name='lease',
            name='early_termination_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lease',
            name='early_termination_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lease',
            name='early_termination_penalty',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),

        # --- Payment: no schema change, status is a @property ---

        # --- MaintenanceRequest: new fields ---
        migrations.AddField(
            model_name='maintenancerequest',
            name='scheduled_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='maintenancerequest',
            name='time_taken',
            field=models.DecimalField(
                blank=True, decimal_places=1, max_digits=5, null=True,
                help_text='Hours taken to resolve'
            ),
        ),
        migrations.AddField(
            model_name='maintenancerequest',
            name='assigned_to',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'role': 'MAINTENANCE'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_maintenance',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
