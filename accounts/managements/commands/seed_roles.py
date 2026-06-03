from django.core.management.base import BaseCommand
from accounts.models import User
from incidents.models import HazardSensor, Incident, EarlyWarning

class Command(BaseCommand):
    help = 'Seeds test users for all roles and sample data'

    def handle(self, *args, **kwargs):
        users = [
            {'username': 'admin_lgu', 'email': 'admin@lgu.gov.ph', 'role': 'LGU_ADMIN', 'first_name': 'Maria', 'last_name': 'Santos', 'municipality': 'Tacloban City', 'contact_number': '09171234567'},
            {'username': 'dispatcher1', 'email': 'dispatcher@lgu.gov.ph', 'role': 'DISPATCHER', 'first_name': 'Juan', 'last_name': 'Cruz', 'municipality': 'Tacloban City', 'contact_number': '09281234567'},
            {'username': 'public_viewer', 'email': 'public@example.com', 'role': 'PUBLIC', 'first_name': 'Ana', 'last_name': 'Reyes', 'municipality': '', 'contact_number': ''},
        ]
        for u in users:
            if not User.objects.filter(username=u['username']).exists():
                user = User.objects.create_user(password='TestPass123!', **u)
                self.stdout.write(self.style.SUCCESS(f'Created: {user.username} ({user.role})'))
            else:
                self.stdout.write(f'Already exists: {u["username"]}')

        # Sample sensors
        sensors_data = [
            {'name': 'Flood Sensor - Brgy. San Jose', 'hazard_type': 'FLOOD', 'status': 'WARNING', 'latitude': 11.2442, 'longitude': 125.0038, 'municipality': 'Tacloban City', 'last_reading': 2.8, 'unit': 'meters'},
            {'name': 'Wind Sensor - PAGASA Station', 'hazard_type': 'TYPHOON', 'status': 'NORMAL', 'latitude': 11.2389, 'longitude': 124.9995, 'municipality': 'Tacloban City', 'last_reading': 45.0, 'unit': 'km/h'},
        ]
        for s in sensors_data:
            HazardSensor.objects.get_or_create(name=s['name'], defaults=s)
            self.stdout.write(self.style.SUCCESS(f'Sensor: {s["name"]}'))

        self.stdout.write(self.style.SUCCESS('\nSeed complete! Credentials:\n  admin_lgu / TestPass123!\n  dispatcher1 / TestPass123!\n  public_viewer / TestPass123!'))