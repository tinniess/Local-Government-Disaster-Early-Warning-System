from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/login/'), name='home'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('public/', views.dashboard_public, name='dashboard_public'),

    # Incidents
    path('incidents/create/', views.incident_create, name='incident_create'),
    path('incidents/<int:pk>/', views.incident_detail, name='incident_detail'),
    path('incidents/<int:pk>/edit/', views.incident_edit, name='incident_edit'),
    path('incidents/<int:pk>/report/', views.incident_report, name='incident_report'),
    path('incidents/bulk-update/', views.bulk_update_status, name='bulk_update'),
    path('map/', views.map_view, name='map'),

    # Warnings
    path('warnings/', views.warning_list, name='warning_list'),
    path('warnings/create/', views.warning_create, name='warning_create'),
    path('warnings/<int:pk>/', views.warning_detail, name='warning_detail'),
    path('warnings/<int:pk>/resolve/', views.resolve_warning, name='warning_resolve'),

    # Sensors
    path('sensors/', views.sensor_list, name='sensor_list'),
    path('sensors/add/', views.sensor_create, name='sensor_create'),
    path('sensors/<int:pk>/', views.sensor_detail, name='sensor_detail'),
    path('sensors/<int:pk>/edit/', views.sensor_edit, name='sensor_edit'),
    path('sensors/<int:pk>/delete/', views.sensor_delete, name='sensor_delete'),

    # Evacuation Centers
    path('evacuation/', views.evacuation_list, name='evacuation_list'),
    path('evacuation/add/', views.evacuation_create, name='evacuation_create'),
    path('evacuation/<int:pk>/edit/', views.evacuation_edit, name='evacuation_edit'),

    # Citizen Reports (public — no login needed)
    path('report/', views.citizen_report_create, name='citizen_report_create'),
    path('report/thanks/', views.citizen_report_thanks, name='citizen_report_thanks'),
    path('report/list/', views.citizen_report_list, name='citizen_report_list'),
    path('report/<int:pk>/validate/', views.citizen_report_validate, name='citizen_report_validate'),

    # Alert Levels
    path('alerts/', views.alert_level_list, name='alert_level_list'),
    path('alerts/set/', views.alert_level_set, name='alert_level_set'),

    # Resources
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/add/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/edit/', views.resource_edit, name='resource_edit'),
]