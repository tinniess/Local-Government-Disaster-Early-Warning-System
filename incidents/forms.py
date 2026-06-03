from django import forms
from django.forms import inlineformset_factory
from django import forms
from .models import Incident
from .models import Incident, HazardImage, EarlyWarning, HazardSensor, CitizenReport, EvacuationCenter, AlertLevel, Resource
from .models import (
    WeatherMonitor,
    HazardMap,
    DamageAssessment,
    AgencyBulletin,
    TaskAssignment,
)

class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'title',
            'hazard_type',
            'severity',
            'municipality',
            'sensor',
            'description',
            'location_details',
            'affected_population'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'hazard_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'location_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sensor': forms.Select(attrs={'class': 'form-select'}),
            'affected_population': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class HazardImageForm(forms.ModelForm):
    class Meta:
        model = HazardImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Caption (optional)'}),
        }

HazardImageFormSet = inlineformset_factory(
    Incident, HazardImage,
    form=HazardImageForm,
    extra=3,
    max_num=10,
    can_delete=True,
)

class EarlyWarningForm(forms.ModelForm):
    class Meta:
        model = EarlyWarning
        fields = ['title', 'message', 'alert_level', 'municipality', 'incident', 'expires_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'alert_level': forms.Select(attrs={'class': 'form-select'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'incident': forms.Select(attrs={'class': 'form-select'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class BulkStatusForm(forms.Form):
    STATUS_CHOICES = Incident.STATUS_CHOICES
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    incident_ids = forms.CharField(widget=forms.HiddenInput)

class IncidentFilterForm(forms.Form):
    HAZARD_CHOICES = [('', 'All Hazards')] + list(HazardSensor.HAZARD_TYPES)
    STATUS_CHOICES = [('', 'All Statuses')] + list(Incident.STATUS_CHOICES)
    SEVERITY_CHOICES = [('', 'All Severities')] + list(Incident.SEVERITY_CHOICES)

    hazard_type = forms.ChoiceField(choices=HAZARD_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))
    severity = forms.ChoiceField(choices=SEVERITY_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date'}))
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Search title, municipality...'}))

class HazardSensorForm(forms.ModelForm):
    class Meta:
        model = HazardSensor
        fields = ['name', 'hazard_type', 'status', 'municipality',
                  'latitude', 'longitude', 'last_reading', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Flood Sensor - Brgy. San Jose'}),
            'hazard_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tacloban City'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'e.g. 11.244200'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'e.g. 125.003800'}),
            'last_reading': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 2.80'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. meters, km/h, magnitude'}),
        }

class CitizenReportForm(forms.ModelForm):
    class Meta:
        model = CitizenReport
        fields = ['report_type', 'description', 'location', 'municipality',
                  'barangay', 'photo', 'reporter_name', 'reporter_contact']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe what you observed...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, landmark, specific location'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'barangay': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'reporter_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'reporter_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile number'}),
        }


class EvacuationCenterForm(forms.ModelForm):
    class Meta:
        model = EvacuationCenter
        fields = ['name', 'address', 'municipality', 'barangay', 'capacity',
                  'current_occupancy', 'status', 'contact_person', 'contact_number',
                  'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'barangay': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_occupancy': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
        }


class AlertLevelForm(forms.ModelForm):
    class Meta:
        model = AlertLevel
        fields = ['hazard_type', 'level', 'municipality', 'description', 'recommended_action']
        widgets = {
            'hazard_type': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommended_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                'placeholder': 'e.g. Prepare go-bag, monitor updates, evacuate if needed...'}),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'resource_type', 'quantity', 'unit', 'status',
                  'location', 'municipality', 'assigned_incident']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. units, kg, liters'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_incident': forms.Select(attrs={'class': 'form-select'}),
        }

class WeatherMonitorForm(forms.ModelForm):
    class Meta:
        model = WeatherMonitor
        fields = ['station_name', 'municipality', 'condition', 'temperature', 'humidity',
                  'rainfall_1h', 'rainfall_24h', 'wind_speed', 'wind_direction',
                  'river_level', 'pagasa_advisory']
        widgets = {
            'station_name': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'humidity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'rainfall_1h': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'rainfall_24h': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'wind_speed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'wind_direction': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. NE, SW'}),
            'river_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pagasa_advisory': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class HazardMapForm(forms.ModelForm):
    class Meta:
        model = HazardMap
        fields = ['name', 'zone_type', 'risk_level', 'municipality', 'barangay',
                  'affected_population', 'description', 'recommended_action']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'zone_type': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'barangay': forms.TextInput(attrs={'class': 'form-control'}),
            'affected_population': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommended_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DamageAssessmentForm(forms.ModelForm):
    class Meta:
        model = DamageAssessment
        fields = ['damage_type', 'severity', 'location', 'municipality', 'barangay',
                  'estimated_cost', 'affected_families', 'affected_persons', 'description', 'photo']
        widgets = {
            'damage_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'barangay': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'affected_families': forms.NumberInput(attrs={'class': 'form-control'}),
            'affected_persons': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class AgencyBulletinForm(forms.ModelForm):
    class Meta:
        model = AgencyBulletin
        fields = ['agency', 'bulletin_type', 'title', 'content', 'source_url', 'issued_at', 'expires_at']
        widgets = {
            'agency': forms.Select(attrs={'class': 'form-select'}),
            'bulletin_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'source_url': forms.URLInput(attrs={'class': 'form-control'}),
            'issued_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class TaskAssignmentForm(forms.ModelForm):
    class Meta:
        model = TaskAssignment
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }