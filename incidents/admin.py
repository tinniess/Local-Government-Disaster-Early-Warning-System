from django.contrib import admin
from .models import Incident, HazardImage, EarlyWarning, HazardSensor
from .models import EvacuationCenter, CitizenReport, AlertLevel, Resource
from .models import WeatherMonitor, HazardMap, DamageAssessment, AgencyBulletin, TaskAssignment

class HazardImageInline(admin.TabularInline):
    model = HazardImage
    extra = 1

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'hazard_type', 'status', 'severity', 'municipality', 'reported_by', 'created_at']
    list_filter = ['status', 'severity', 'hazard_type', 'municipality']
    search_fields = ['title', 'description', 'municipality']
    inlines = [HazardImageInline]
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_monitoring']

    def mark_resolved(self, request, queryset):
        queryset.update(status='RESOLVED')
    mark_resolved.short_description = 'Mark selected as Resolved'

    def mark_monitoring(self, request, queryset):
        queryset.update(status='MONITORING')
    mark_monitoring.short_description = 'Mark selected as Monitoring'

@admin.register(HazardSensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ['name', 'hazard_type', 'status', 'municipality', 'last_reading', 'updated_at']
    list_filter = ['status', 'hazard_type', 'municipality']

@admin.register(EarlyWarning)
class EarlyWarningAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_level', 'municipality', 'is_active', 'issued_by', 'created_at']
    list_filter = ['alert_level', 'is_active']

@admin.register(EvacuationCenter)
class EvacuationCenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'municipality', 'barangay', 'status', 'current_occupancy', 'capacity', 'updated_at']
    list_filter = ['status', 'municipality']
    search_fields = ['name', 'municipality', 'barangay']

@admin.register(CitizenReport)
class CitizenReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'location', 'municipality', 'reporter_name', 'status', 'submitted_at']
    list_filter = ['status', 'report_type', 'municipality']
    search_fields = ['description', 'location', 'reporter_name']

@admin.register(AlertLevel)
class AlertLevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'hazard_type', 'municipality', 'is_active', 'set_by', 'created_at']
    list_filter = ['level', 'hazard_type', 'is_active']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'resource_type', 'quantity', 'unit', 'status', 'municipality', 'updated_at']
    list_filter = ['status', 'resource_type', 'municipality']
    search_fields = ['name', 'location']

@admin.register(WeatherMonitor)
class WeatherMonitorAdmin(admin.ModelAdmin):
    list_display = ['station_name', 'municipality', 'condition', 'temperature', 'rainfall_1h', 'wind_speed', 'updated_at']
    list_filter = ['condition', 'municipality']

@admin.register(HazardMap)
class HazardMapAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone_type', 'risk_level', 'municipality', 'barangay', 'affected_population']
    list_filter = ['zone_type', 'risk_level', 'municipality']

@admin.register(DamageAssessment)
class DamageAssessmentAdmin(admin.ModelAdmin):
    list_display = ['damage_type', 'severity', 'municipality', 'affected_families', 'estimated_cost', 'assessed_at']
    list_filter = ['damage_type', 'severity', 'municipality']

@admin.register(AgencyBulletin)
class AgencyBulletinAdmin(admin.ModelAdmin):
    list_display = ['agency', 'bulletin_type', 'title', 'is_active', 'issued_at']
    list_filter = ['agency', 'bulletin_type', 'is_active']

@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'incident', 'assigned_to', 'priority', 'status', 'due_date']
    list_filter = ['status', 'priority']

# Register your models here.
