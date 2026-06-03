from django.shortcuts import render
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q
from django.db import models
from .models import Incident, EarlyWarning, HazardSensor, EvacuationCenter, CitizenReport, AlertLevel, Resource
from django.shortcuts import get_object_or_404, redirect
from .models import EarlyWarning
from django.contrib.auth.decorators import login_required
from .forms import (
    IncidentForm, HazardImageFormSet, EarlyWarningForm,
    BulkStatusForm, IncidentFilterForm, CitizenReportForm,
    EvacuationCenterForm, AlertLevelForm, ResourceForm, HazardSensorForm
)
from .models import (
    HazardImage,
    WeatherMonitor,
    HazardMap,
    DamageAssessment,
    AgencyBulletin,
    TaskAssignment,
)
import json
from django.shortcuts import render

audit = logging.getLogger('audit')

def get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0] if x else request.META.get('REMOTE_ADDR', 'unknown')

@login_required
def dashboard(request):
    user = request.user

    # RBAC — strict queryset per role
    if user.is_lgu_admin():
        qs = Incident.objects.all()
    elif user.is_dispatcher():
        view_all = request.GET.get('view') == 'all'
        qs = Incident.objects.all() if view_all else Incident.objects.filter(reported_by=user)
    else:
        # Public Viewer — read-only, active/monitoring only
        qs = Incident.objects.filter(status__in=['ACTIVE', 'MONITORING'])

    # Advanced filtering
    filter_form = IncidentFilterForm(request.GET or None)
    if filter_form.is_valid():
        d = filter_form.cleaned_data
        if d.get('hazard_type'):
            qs = qs.filter(hazard_type=d['hazard_type'])
        if d.get('status'):
            qs = qs.filter(status=d['status'])
        if d.get('severity'):
            qs = qs.filter(severity=d['severity'])
        if d.get('date_from'):
            qs = qs.filter(created_at__date__gte=d['date_from'])
        if d.get('date_to'):
            qs = qs.filter(created_at__date__lte=d['date_to'])
        if d.get('search'):
            qs = qs.filter(
                Q(title__icontains=d['search']) |
                Q(municipality__icontains=d['search']) |
                Q(description__icontains=d['search'])
            )

    # Pagination — preserves filters
    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    incidents = paginator.get_page(page)

    sensors = HazardSensor.objects.all()
    active_warnings = EarlyWarning.objects.filter(is_active=True).order_by('-created_at')[:5]

    # Stats
    base_qs = Incident.objects.all() if user.is_lgu_admin() else qs
    stats = {
        'total': base_qs.count(),
        'active': base_qs.filter(status='ACTIVE').count(),
        'critical': base_qs.filter(severity='CRITICAL').count(),
        'resolved': base_qs.filter(status='RESOLVED').count(),
    }

    # Strip page param so pagination links don't double-up
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'incidents/dashboard.html', {
        'incidents': incidents,
        'filter_form': filter_form,
        'sensors': sensors,
        'active_warnings': active_warnings,
        'stats': stats,
        'request_get': params.urlencode(),
    })


@login_required
def incident_create(request):
    if request.user.is_public():
        audit.warning(f'UNAUTHORIZED_ACCESS | user={request.user.username} | action=incident_create | ip={get_client_ip(request)} | ts={timezone.now()}')
        return HttpResponseForbidden('Public Viewers cannot log incidents.')

    form = IncidentForm(request.POST or None, request.FILES or None)
    formset = HazardImageFormSet(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            incident = form.save(commit=False)
            incident.reported_by = request.user
            incident.save()
            formset.instance = incident
            formset.save()
            audit.info(f'INCIDENT_CREATED | user={request.user.username} | incident_id={incident.id} | title={incident.title} | severity={incident.severity} | ts={timezone.now()}')
            messages.success(request, f'Incident "{incident.title}" logged successfully.')
            return redirect('incident_detail', pk=incident.pk)
        else:
            print(form.errors)
            print(formset.errors)
            print(formset.non_form_errors())
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'incidents/incident_form.html', {
        'form': form,
        'formset': formset,
        'action': 'Log',

    })


@login_required
def incident_detail(request, pk):
    user = request.user

    # Anti-IDOR: enforce ownership per role
    if user.is_lgu_admin():
        incident = get_object_or_404(Incident, pk=pk)
    elif user.is_dispatcher():
        incident = get_object_or_404(Incident, pk=pk, reported_by=user)
        if not Incident.objects.filter(pk=pk).exists():
            return HttpResponseForbidden()
    else:
        # Public can only see active/monitoring
        incident = get_object_or_404(Incident, pk=pk, status__in=['ACTIVE', 'MONITORING'])

    audit.info(f'INCIDENT_VIEW | user={user.username} | role={user.role} | incident_id={pk} | ts={timezone.now()}')
    return render(request, 'incidents/incident_detail.html', {'incident': incident})


@login_required
def incident_edit(request, pk):
    user = request.user

    if user.is_lgu_admin():
        incident = get_object_or_404(Incident, pk=pk)
    elif user.is_dispatcher():
        incident = get_object_or_404(Incident, pk=pk, reported_by=user)
    else:
        audit.warning(f'IDOR_ATTEMPT | user={user.username} | action=edit | incident_id={pk} | ip={get_client_ip(request)} | ts={timezone.now()}')
        return HttpResponseForbidden('Access denied.')

    form = IncidentForm(request.POST or None, request.FILES or None, instance=incident)
    formset = HazardImageFormSet(request.POST or None, request.FILES or None, instance=incident)

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            audit.info(f'INCIDENT_UPDATED | user={user.username} | incident_id={pk} | ts={timezone.now()}')
            messages.success(request, 'Incident updated successfully.')
            return redirect('incident_detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'incidents/incident_form.html', {
        'form': form,
        'formset': formset,
        'incident': incident,
        'action': 'Edit',
    })


@login_required
def bulk_update_status(request):
    # Strict: LGU Admin only
    if not request.user.is_lgu_admin():
        audit.warning(f'UNAUTHORIZED_BULK | user={request.user.username} | ip={get_client_ip(request)} | ts={timezone.now()}')
        return HttpResponseForbidden('LGU Admin access required for bulk operations.')

    if request.method == 'POST':
        form = BulkStatusForm(request.POST)
        if form.is_valid():
            raw_ids = form.cleaned_data['incident_ids']
            ids = [i.strip() for i in raw_ids.split(',') if i.strip().isdigit()]
            new_status = form.cleaned_data['status']
            if ids and new_status:
                updated = Incident.objects.filter(id__in=ids).update(status=new_status)
                audit.info(f'BULK_STATUS_UPDATE | user={request.user.username} | ids={ids} | new_status={new_status} | count={updated} | ts={timezone.now()}')
                messages.success(request, f'{updated} incident(s) updated to "{new_status}".')
            else:
                messages.error(request, 'Select incidents and a status.')
    return redirect('dashboard')


@login_required
def warning_create(request):
    if request.user.is_public():
        return HttpResponseForbidden('Access denied.')

    form = EarlyWarningForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        warning = form.save(commit=False)
        warning.issued_by = request.user
        warning.save()
        audit.info(f'WARNING_ISSUED | user={request.user.username} | warning_id={warning.id} | level={warning.alert_level} | municipality={warning.municipality or "ALL"} | ts={timezone.now()}')
        messages.success(request, f'Early warning "{warning.title}" broadcast successfully.')
        return redirect('dashboard')

    return render(request, 'incidents/warning_form.html', {'form': form})

def resolve_warning(request, pk):
    warning = get_object_or_404(EarlyWarning, pk=pk)
    warning.is_active = False
    warning.save()
    return redirect('dashboard')


@login_required
def sensor_list(request):
    sensors = HazardSensor.objects.all().order_by('status', 'hazard_type')
    return render(request, 'incidents/sensor_list.html', {'sensors': sensors})


@login_required
def warning_list(request):
    warnings = EarlyWarning.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'incidents/warning_list.html', {'warnings': warnings})

@login_required
def sensor_create(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden('LGU Admin access required.')
    from .forms import HazardSensorForm
    form = HazardSensorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        sensor = form.save()
        audit.info(f'SENSOR_CREATED | user={request.user.username} | sensor_id={sensor.id} | name={sensor.name} | ts={timezone.now()}')
        messages.success(request, f'Sensor "{sensor.name}" added successfully.')
        return redirect('sensor_list')
    return render(request, 'incidents/sensor_form.html', {'form': form, 'action': 'Add'})


@login_required
def sensor_edit(request, pk):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden('LGU Admin access required.')
    sensor = get_object_or_404(HazardSensor, pk=pk)
    from .forms import HazardSensorForm
    form = HazardSensorForm(request.POST or None, instance=sensor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        audit.info(f'SENSOR_UPDATED | user={request.user.username} | sensor_id={pk} | ts={timezone.now()}')
        messages.success(request, f'Sensor "{sensor.name}" updated.')
        return redirect('sensor_list')
    return render(request, 'incidents/sensor_form.html', {'form': form, 'action': 'Edit', 'sensor': sensor})


@login_required
def sensor_delete(request, pk):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden('LGU Admin access required.')
    sensor = get_object_or_404(HazardSensor, pk=pk)
    if request.method == 'POST':
        name = sensor.name
        sensor.delete()
        audit.info(f'SENSOR_DELETED | user={request.user.username} | sensor_id={pk} | name={name} | ts={timezone.now()}')
        messages.success(request, f'Sensor "{name}" deleted.')
        return redirect('sensor_list')
    return render(request, 'incidents/sensor_confirm_delete.html', {'sensor': sensor})

# ─── EVACUATION CENTERS ───────────────────────────────────────────────
@login_required
def evacuation_list(request):
    centers = EvacuationCenter.objects.all()
    return render(request, 'incidents/evacuation_list.html', {'centers': centers})

@login_required
def evacuation_create(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    from .forms import EvacuationCenterForm
    form = EvacuationCenterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        center = form.save()
        audit.info(f'EVACUATION_CENTER_CREATED | user={request.user.username} | id={center.id} | name={center.name} | ts={timezone.now()}')
        messages.success(request, f'Evacuation center "{center.name}" added.')
        return redirect('evacuation_list')
    return render(request, 'incidents/evacuation_form.html', {'form': form, 'action': 'Add'})

@login_required
def evacuation_edit(request, pk):
    if not (request.user.is_lgu_admin() or request.user.is_dispatcher()):
        return HttpResponseForbidden()
    center = get_object_or_404(EvacuationCenter, pk=pk)
    from .forms import EvacuationCenterForm
    form = EvacuationCenterForm(request.POST or None, instance=center)
    if request.method == 'POST' and form.is_valid():
        form.save()
        audit.info(f'EVACUATION_CENTER_UPDATED | user={request.user.username} | id={pk} | ts={timezone.now()}')
        messages.success(request, 'Evacuation center updated.')
        return redirect('evacuation_list')
    return render(request, 'incidents/evacuation_form.html', {'form': form, 'action': 'Edit', 'center': center})


# ─── CITIZEN REPORTS ──────────────────────────────────────────────────
def citizen_report_create(request):
    """Public — no login required"""
    form = CitizenReportForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save()
        audit.info(f'CITIZEN_REPORT_SUBMITTED | reporter={report.reporter_name} | type={report.report_type} | location={report.location} | ts={timezone.now()}')
        messages.success(request, 'Your report has been submitted. Thank you for helping your community!')
        return redirect('citizen_report_thanks')
    return render(request, 'incidents/citizen_report_form.html', {'form': form})

def citizen_report_thanks(request):
    return render(request, 'incidents/citizen_report_thanks.html')

@login_required
def citizen_report_list(request):
    if not (request.user.is_lgu_admin() or request.user.is_dispatcher()):
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    reports = CitizenReport.objects.all()
    if status_filter:
        reports = reports.filter(status=status_filter)
    return render(request, 'incidents/citizen_report_list.html', {'reports': reports, 'status_filter': status_filter})

@login_required
def citizen_report_validate(request, pk):
    if not (request.user.is_lgu_admin() or request.user.is_dispatcher()):
        return HttpResponseForbidden()
    report = get_object_or_404(CitizenReport, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'verify':
            report.status = 'VERIFIED'
        elif action == 'reject':
            report.status = 'REJECTED'
        elif action == 'resolve':
            report.status = 'RESOLVED'
        report.validated_by = request.user
        report.save()
        audit.info(f'CITIZEN_REPORT_VALIDATED | user={request.user.username} | report_id={pk} | action={action} | ts={timezone.now()}')
        messages.success(request, f'Report marked as {report.get_status_display()}.')
    return redirect('citizen_report_list')


# ─── ALERT LEVELS ─────────────────────────────────────────────────────
@login_required
def alert_level_list(request):
    levels = AlertLevel.objects.filter(is_active=True).order_by('municipality', 'hazard_type')
    return render(request, 'incidents/alert_level_list.html', {'levels': levels})

@login_required
def alert_level_set(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    from .forms import AlertLevelForm
    form = AlertLevelForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        level = form.save(commit=False)
        level.set_by = request.user
        level.save()
        audit.info(f'ALERT_LEVEL_SET | user={request.user.username} | level={level.level} | hazard={level.hazard_type} | municipality={level.municipality} | ts={timezone.now()}')
        messages.success(request, f'Alert level set to {level.level} for {level.municipality}.')
        return redirect('alert_level_list')
    return render(request, 'incidents/alert_level_form.html', {'form': form})


# ─── RESOURCES ────────────────────────────────────────────────────────
@login_required
def resource_list(request):
    resources = Resource.objects.all()
    return render(request, 'incidents/resource_list.html', {'resources': resources})

@login_required
def resource_create(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    from .forms import ResourceForm
    form = ResourceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        resource = form.save(commit=False)
        resource.managed_by = request.user
        resource.save()
        audit.info(f'RESOURCE_CREATED | user={request.user.username} | id={resource.id} | name={resource.name} | ts={timezone.now()}')
        messages.success(request, f'Resource "{resource.name}" added.')
        return redirect('resource_list')
    return render(request, 'incidents/resource_form.html', {'form': form, 'action': 'Add'})

@login_required
def resource_edit(request, pk):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    resource = get_object_or_404(Resource, pk=pk)
    from .forms import ResourceForm
    form = ResourceForm(request.POST or None, instance=resource)
    if request.method == 'POST' and form.is_valid():
        form.save()
        audit.info(f'RESOURCE_UPDATED | user={request.user.username} | id={pk} | ts={timezone.now()}')
        messages.success(request, 'Resource updated.')
        return redirect('resource_list')
    return render(request, 'incidents/resource_form.html', {'form': form, 'action': 'Edit', 'resource': resource})

# ─── PUBLIC DASHBOARD ─────────────────────────────────────────────────
@login_required
def dashboard_public(request):
    """Enhanced public dashboard with all situational info"""
    incidents = Incident.objects.filter(
        status__in=['ACTIVE', 'MONITORING']
    ).order_by('-created_at')[:10]

    active_warnings = EarlyWarning.objects.filter(is_active=True).order_by('-created_at')
    alert_levels = AlertLevel.objects.filter(is_active=True).order_by('level')
    evacuation_centers = EvacuationCenter.objects.all().order_by('status')
    open_centers = EvacuationCenter.objects.filter(status='OPEN').count()
    sensor_warnings = HazardSensor.objects.filter(
        status__in=['WARNING', 'CRITICAL']
    ).count()

    stats = {
        'active': Incident.objects.filter(status='ACTIVE').count(),
    }

    return render(request, 'incidents/dashboard_public.html', {
        'incidents': incidents,
        'active_warnings': active_warnings,
        'alert_levels': alert_levels,
        'evacuation_centers': evacuation_centers,
        'open_centers': open_centers,
        'sensor_warnings': sensor_warnings,
        'stats': stats,
    })


# ─── INCIDENT REPORT (PRINTABLE) ─────────────────────────────────────
@login_required
def incident_report(request, pk):
    if request.user.is_lgu_admin():
        incident = get_object_or_404(Incident, pk=pk)
    elif request.user.is_dispatcher():
        incident = get_object_or_404(Incident, pk=pk, reported_by=request.user)
    else:
        incident = get_object_or_404(Incident, pk=pk, status__in=['ACTIVE', 'MONITORING'])
    return render(request, 'incidents/incident_report.html', {'incident': incident})


# ─── WARNING DETAIL ───────────────────────────────────────────────────
@login_required
def warning_detail(request, pk):
    warning = get_object_or_404(EarlyWarning, pk=pk)
    return render(request, 'incidents/warning_detail.html', {'warning': warning})


# ─── SENSOR DETAIL ────────────────────────────────────────────────────
@login_required
def sensor_detail(request, pk):
    sensor = get_object_or_404(HazardSensor, pk=pk)
    linked_incidents = Incident.objects.filter(sensor=sensor).order_by('-created_at')[:5]
    return render(request, 'incidents/sensor_detail.html', {
        'sensor': sensor,
        'linked_incidents': linked_incidents,
    })

# ─── WEATHER MONITORING ──────────────────────────────────────────────
@login_required
def weather_list(request):
    stations = WeatherMonitor.objects.all()
    return render(request, 'incidents/weather_list.html', {'stations': stations})

@login_required
def weather_update(request, pk=None):
    if not (request.user.is_lgu_admin() or request.user.is_dispatcher()):
        return HttpResponseForbidden()
    from .forms import WeatherMonitorForm
    instance = get_object_or_404(WeatherMonitor, pk=pk) if pk else None
    form = WeatherMonitorForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        station = form.save()
        audit.info(f'WEATHER_UPDATED | user={request.user.username} | station={station.station_name} | ts={timezone.now()}')
        messages.success(request, f'Weather data for "{station.station_name}" updated.')
        return redirect('weather_list')
    return render(request, 'incidents/weather_form.html', {'form': form, 'action': 'Update' if pk else 'Add'})


# ─── HAZARD MAPS ─────────────────────────────────────────────────────
@login_required
def hazard_map_list(request):
    zones = HazardMap.objects.all()
    return render(request, 'incidents/hazard_map_list.html', {'zones': zones})

@login_required
def hazard_map_create(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    from .forms import HazardMapForm
    form = HazardMapForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        zone = form.save(commit=False)
        zone.created_by = request.user
        zone.save()
        audit.info(f'HAZARD_MAP_CREATED | user={request.user.username} | name={zone.name} | ts={timezone.now()}')
        messages.success(request, f'Hazard zone "{zone.name}" added.')
        return redirect('hazard_map_list')
    return render(request, 'incidents/hazard_map_form.html', {'form': form, 'action': 'Add'})


# ─── DAMAGE ASSESSMENT ───────────────────────────────────────────────
@login_required
def damage_assessment_create(request, incident_pk):
    if not (request.user.is_lgu_admin() or request.user.is_dispatcher()):
        return HttpResponseForbidden()
    incident = get_object_or_404(Incident, pk=incident_pk)
    from .forms import DamageAssessmentForm
    form = DamageAssessmentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        da = form.save(commit=False)
        da.incident = incident
        da.assessed_by = request.user
        da.save()
        audit.info(f'DAMAGE_ASSESSED | user={request.user.username} | incident_id={incident_pk} | type={da.damage_type} | ts={timezone.now()}')
        messages.success(request, 'Damage assessment recorded.')
        return redirect('incident_detail', pk=incident_pk)
    return render(request, 'incidents/damage_assessment_form.html', {
        'form': form, 'incident': incident
    })


# ─── AGENCY BULLETINS ────────────────────────────────────────────────
@login_required
def bulletin_list(request):
    bulletins = AgencyBulletin.objects.filter(is_active=True)
    return render(request, 'incidents/bulletin_list.html', {'bulletins': bulletins})

@login_required
def bulletin_create(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    from .forms import AgencyBulletinForm
    form = AgencyBulletinForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        bulletin = form.save(commit=False)
        bulletin.created_by = request.user
        bulletin.save()
        audit.info(f'BULLETIN_CREATED | user={request.user.username} | agency={bulletin.agency} | ts={timezone.now()}')
        messages.success(request, 'Agency bulletin posted.')
        return redirect('bulletin_list')
    return render(request, 'incidents/bulletin_form.html', {'form': form})


# ─── TASK ASSIGNMENTS ────────────────────────────────────────────────
@login_required
def task_list(request):
    if request.user.is_lgu_admin():
        tasks = TaskAssignment.objects.all()
    else:
        tasks = TaskAssignment.objects.filter(assigned_to=request.user)
    return render(request, 'incidents/task_list.html', {'tasks': tasks})

@login_required
def task_create(request, incident_pk):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    incident = get_object_or_404(Incident, pk=incident_pk)
    from .forms import TaskAssignmentForm
    from accounts.models import User
    form = TaskAssignmentForm(request.POST or None)
    form.fields['assigned_to'].queryset = User.objects.filter(
        role__in=['LGU_ADMIN', 'DISPATCHER'], is_active=True
    )
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.incident = incident
        task.assigned_by = request.user
        task.save()
        audit.info(f'TASK_ASSIGNED | by={request.user.username} | to={task.assigned_to} | incident={incident_pk} | ts={timezone.now()}')
        messages.success(request, f'Task "{task.title}" assigned to {task.assigned_to}.')
        return redirect('incident_detail', pk=incident_pk)
    return render(request, 'incidents/task_form.html', {'form': form, 'incident': incident})

@login_required
def task_update_status(request, pk):
    task = get_object_or_404(TaskAssignment, pk=pk)
    if task.assigned_to != request.user and not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            task.status = new_status
            if new_status == 'COMPLETED':
                task.completed_at = timezone.now()
            task.save()
            audit.info(f'TASK_STATUS_UPDATED | user={request.user.username} | task_id={pk} | status={new_status} | ts={timezone.now()}')
            messages.success(request, f'Task marked as {new_status}.')
    return redirect('task_list')


# ─── ANALYTICS DASHBOARD ─────────────────────────────────────────────
@login_required
def analytics(request):
    if not request.user.is_lgu_admin():
        return HttpResponseForbidden()
    from django.db.models import Count
    incidents_by_hazard = list(Incident.objects.values('hazard_type').annotate(count=Count('id')).order_by('-count'))
    incidents_by_status = list(Incident.objects.values('status').annotate(count=Count('id')))
    incidents_by_severity = list(Incident.objects.values('severity').annotate(count=Count('id')))
    citizen_by_status = list(CitizenReport.objects.values('status').annotate(count=Count('id')))
    total_affected = sum(i.affected_population for i in Incident.objects.all())
    total_damage = DamageAssessment.objects.filter(
        estimated_cost__isnull=False
    ).aggregate(total=models.Sum('estimated_cost'))['total'] or 0

    return render(request, 'incidents/analytics.html', {
        'incidents_by_hazard': incidents_by_hazard,
        'incidents_by_status': incidents_by_status,
        'incidents_by_severity': incidents_by_severity,
        'citizen_by_status': citizen_by_status,
        'total_affected': total_affected,
        'total_damage': total_damage,
        'total_incidents': Incident.objects.count(),
        'total_warnings': EarlyWarning.objects.count(),
        'total_sensors': HazardSensor.objects.count(),
        'active_tasks': TaskAssignment.objects.filter(status__in=['PENDING', 'IN_PROGRESS']).count(),
    })

def map_view(request):
    incidents = Incident.objects.exclude(latitude=None, longitude=None)

    data = []
    for i in incidents:
        data.append({
            'title': i.title,
            'lat': i.latitude,
            'lng': i.longitude,
            'severity': i.severity,
        })

    return render(request, 'incidents/map.html', {
        'incidents': json.dumps(data)
    })