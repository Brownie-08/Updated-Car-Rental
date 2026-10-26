import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo_settings')
os.environ.setdefault('SECRET_KEY', 'local-check-only-not-a-deployment-secret')
import django
django.setup()
from django.test import Client
from system.models import Car

client = Client()
for path in ('/demo/', '/demo/health/', '/', '/car/carlist/', '/car/1/', '/demo/start/', '/car/newcar/', '/demo/admin/', '/admin/', '/admin/system/car/'):
    response = client.get(path)
    assert response.status_code in (200, 302), (path, response.status_code)
    print(path, response.status_code)
before = Car.objects.count()
assert client.post('/create/', {'car_name': 'unwanted'}).status_code == 403
assert client.get('/car/1/delete/').status_code == 403
assert client.get('/admin_register/').status_code == 403
assert client.get('/car/debug/').status_code == 403
assert Car.objects.count() == before
print('Public demo routes work; write and debug routes blocked.')
