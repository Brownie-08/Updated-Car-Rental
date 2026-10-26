"""Idempotently add synthetic demo records; never import a production database."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo_settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from system.models import Car, Order
from datetime import date, timedelta

user, _ = get_user_model().objects.get_or_create(username='demo_reviewer', defaults={'email': 'reviewer@example.invalid', 'first_name': 'Demo', 'last_name': 'Reviewer', 'email_verified': True, 'is_staff': True, 'is_active': True})
user.set_unusable_password()
user.is_staff = True
user.is_superuser = False
user.save()
user.user_permissions.set(Permission.objects.filter(codename__startswith='view_'))
for name, company, seats, price in [('Demo Executive Sedan', 'Sample Motors', 5, '85.00'), ('Demo Family SUV', 'Sample Motors', 7, '120.00'), ('Demo City Compact', 'Sample Motors', 4, '55.00')]:
    Car.objects.update_or_create(car_name=name, defaults={'company_name': company, 'num_of_seats': seats, 'cost_par_day': price, 'content': 'Synthetic portfolio listing. This vehicle is not available for real rental.', 'image': 'sample-car.svg', 'height_field': 540, 'width_field': 900})
Order.objects.get_or_create(order_number='DEMO-BOOKING-001', defaults={'customer': user, 'car_name': 'Demo Executive Sedan', 'dealer_name': 'Sample Motors', 'cell_no': '0000000000', 'address': 'Demo location only', 'date_from': date.today(), 'date_to': date.today() + timedelta(days=2), 'daily_rate': '85.00', 'status': 'confirmed'})
print('Synthetic demo data ready.')
