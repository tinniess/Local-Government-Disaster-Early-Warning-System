from django.db import models
from django.conf import settings 
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class HazardSensor(models.Model):
    HAZARD_TYPES = [
        ('FLOOD', 'Flood'),
        ('TYPHOON', 'Typhoon'),
        ('LANDSLIDE', 'Landslide'),
        ('EARTHQUAKE', 'Earthquake'),
        ('FIRE', 'Fire'),
        ('STORM_SURGE', 'Storm Surge'),
    ]
    STATUS_CHOICES = [
        ('NORMAL', 'Normal'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
        ('OFFLINE', 'Offline'),
    ]
    name = models.CharField(max_length=100)
    hazard_type = models.CharField(max_length=20, choices=HAZARD_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NORMAL')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    municipality = models.CharField(max_length=100)
    last_reading = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True, help_text='e.g. mm, m/s, magnitude')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} [{self.get_status_display()}]'

    class Meta:
        ordering = ['-updated_at']


class Incident(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('MONITORING', 'Monitoring'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    hazard_type = models.CharField(max_length=20, choices=HazardSensor.HAZARD_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MODERATE')
    municipality = models.CharField(max_length=100)
    image = models.ImageField(upload_to="hazards/", null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    location_details = models.TextField(help_text='Street, barangay, landmarks')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    sensor = models.ForeignKey(
        HazardSensor, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='incidents'
    )
    affected_population = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'[{self.get_status_display()}] {self.title}'

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_bulk_update', 'Can bulk update incident status'),
            ('can_view_all', 'Can view all incidents'),
        ]


class HazardImage(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="hazards/", null=True, blank=True)
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Image for {self.incident.title}'


class EarlyWarning(models.Model):
    ALERT_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('DANGER', 'Danger'),
        ('CRITICAL', 'Critical'),
    ]
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS, default='WARNING')
    municipality = models.CharField(max_length=100, blank=True, help_text='Leave blank for all municipalities')
    incident = models.ForeignKey(Incident, on_delete=models.SET_NULL, null=True, blank=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'[{self.get_alert_level_display()}] {self.title}'

    class Meta:
        ordering = ['-created_at']

class EvacuationCenter(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('FULL', 'Full'),
        ('CLOSED', 'Closed'),
        ('STANDBY', 'On Standby'),
    ]
    name = models.CharField(max_length=200)
    address = models.TextField()
    municipality = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=0)
    current_occupancy = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='STANDBY')
    contact_person = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def occupancy_percentage(self):
        if self.capacity > 0:
            return round((self.current_occupancy / self.capacity) * 100)
        return 0

    def available_slots(self):
        return max(0, self.capacity - self.current_occupancy)

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    class Meta:
        ordering = ['municipality', 'name']


class CitizenReport(models.Model):
    REPORT_TYPES = [
        ('FLOOD', 'Flood'),
        ('FIRE', 'Fire'),
        ('LANDSLIDE', 'Landslide'),
        ('DAMAGE', 'Structural Damage'),
        ('RESCUE', 'Rescue Needed'),
        ('ROAD', 'Road Blocked'),
        ('OTHER', 'Other'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Validation'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('RESOLVED', 'Resolved'),
    ]
    report_type = models.CharField(max_length=15, choices=REPORT_TYPES)
    description = models.TextField()
    location = models.TextField()
    municipality = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='citizen_reports/', blank=True, null=True)
    reporter_name = models.CharField(max_length=100)
    reporter_contact = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='validated_reports'
    )
    linked_incident = models.ForeignKey(
        Incident, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='citizen_reports'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'[{self.get_status_display()}] {self.get_report_type_display()} — {self.location}'

    class Meta:
        ordering = ['-submitted_at']


class AlertLevel(models.Model):
    LEVEL_CHOICES = [
        ('GREEN', 'Green — Normal'),
        ('YELLOW', 'Yellow — Advisory'),
        ('ORANGE', 'Orange — Warning'),
        ('RED', 'Red — Danger'),
    ]
    hazard_type = models.CharField(max_length=20, choices=HazardSensor.HAZARD_TYPES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='GREEN')
    municipality = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.level} — {self.get_hazard_type_display()} ({self.municipality})'

    class Meta:
        ordering = ['-created_at']


class Resource(models.Model):
    RESOURCE_TYPES = [
        ('VEHICLE', 'Rescue Vehicle'),
        ('MEDICAL', 'Medical Supply'),
        ('FOOD', 'Food & Water'),
        ('RESCUE_TEAM', 'Rescue Team'),
        ('EQUIPMENT', 'Equipment'),
        ('SHELTER', 'Shelter Supply'),
    ]
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('DEPLOYED', 'Deployed'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('EXHAUSTED', 'Exhausted'),
    ]
    name = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=15, choices=RESOURCE_TYPES)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=50, blank=True, help_text='e.g. units, kg, liters')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AVAILABLE')
    location = models.CharField(max_length=200, blank=True)
    municipality = models.CharField(max_length=100)
    assigned_incident = models.ForeignKey(
        Incident, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resources'
    )
    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} [{self.get_status_display()}]'

    class Meta:
        ordering = ['resource_type', 'name']

class WeatherMonitor(models.Model):
    CONDITION_CHOICES = [
        ('CLEAR', 'Clear'),
        ('CLOUDY', 'Cloudy'),
        ('RAINY', 'Rainy'),
        ('STORMY', 'Stormy'),
        ('TYPHOON', 'Typhoon'),
    ]
    station_name = models.CharField(max_length=200)
    municipality = models.CharField(max_length=100)
    temperature = models.FloatField(null=True, blank=True, help_text='°C')
    humidity = models.FloatField(null=True, blank=True, help_text='%')
    rainfall_1h = models.FloatField(null=True, blank=True, help_text='mm/hr')
    rainfall_24h = models.FloatField(null=True, blank=True, help_text='mm/24hr')
    wind_speed = models.FloatField(null=True, blank=True, help_text='km/h')
    wind_direction = models.CharField(max_length=10, blank=True)
    river_level = models.FloatField(null=True, blank=True, help_text='meters')
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='CLEAR')
    pagasa_advisory = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.station_name} — {self.get_condition_display()}'

    class Meta:
        ordering = ['-updated_at']


class HazardMap(models.Model):
    ZONE_TYPES = [
        ('FLOOD', 'Flood Zone'),
        ('LANDSLIDE', 'Landslide Zone'),
        ('STORM_SURGE', 'Storm Surge Zone'),
        ('EARTHQUAKE', 'Earthquake Fault Zone'),
        ('TSUNAMI', 'Tsunami Zone'),
        ('FIRE', 'Fire-Prone Zone'),
    ]
    RISK_LEVELS = [
        ('LOW', 'Low Risk'),
        ('MODERATE', 'Moderate Risk'),
        ('HIGH', 'High Risk'),
        ('VERY_HIGH', 'Very High Risk'),
    ]
    name = models.CharField(max_length=200)
    zone_type = models.CharField(max_length=15, choices=ZONE_TYPES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    municipality = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100, blank=True)
    affected_population = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} — {self.get_risk_level_display()}'

    class Meta:
        ordering = ['-risk_level', 'municipality']


class DamageAssessment(models.Model):
    DAMAGE_TYPES = [
        ('HOUSE', 'House/Structure'),
        ('ROAD', 'Road/Bridge'),
        ('FARM', 'Agricultural'),
        ('INFRA', 'Infrastructure'),
        ('LIVELIHOOD', 'Livelihood'),
    ]
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('MAJOR', 'Major'),
        ('TOTAL', 'Total Loss'),
    ]
    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name='damage_assessments'
    )
    damage_type = models.CharField(max_length=15, choices=DAMAGE_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    location = models.TextField()
    municipality = models.CharField(max_length=100)
    barangay = models.CharField(max_length=100, blank=True)
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    affected_families = models.PositiveIntegerField(default=0)
    affected_persons = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='damage_assessments/', blank=True, null=True)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    assessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_damage_type_display()} — {self.severity} ({self.municipality})'

    class Meta:
        ordering = ['-assessed_at']


class AgencyBulletin(models.Model):
    AGENCY_CHOICES = [
        ('PAGASA', 'PAGASA'),
        ('PHIVOLCS', 'PHIVOLCS'),
        ('NDRRMC', 'NDRRMC'),
        ('LDRRMO', 'LDRRMO'),
        ('OTHER', 'Other Agency'),
    ]
    BULLETIN_TYPES = [
        ('ADVISORY', 'Advisory'),
        ('WATCH', 'Watch'),
        ('WARNING', 'Warning'),
        ('BULLETIN', 'Bulletin'),
        ('FORECAST', 'Forecast'),
    ]
    agency = models.CharField(max_length=10, choices=AGENCY_CHOICES)
    bulletin_type = models.CharField(max_length=10, choices=BULLETIN_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    source_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'[{self.agency}] {self.title}'

    class Meta:
        ordering = ['-issued_at']


class TaskAssignment(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_tasks'
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} → {self.assigned_to}'

    class Meta:
        ordering = ['-created_at']

# Create your models here.
