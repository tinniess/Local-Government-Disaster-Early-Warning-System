from django.shortcuts import render
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from incidents.models import Incident, HazardSensor, EarlyWarning
from accounts.models import User
from django.shortcuts import get_object_or_404, redirect
from .serializers import (
    IncidentSerializer, SensorSerializer,
    EarlyWarningSerializer, UserSerializer
)
from .permissions import IsLGUAdminOrReadOnly, IsDispatcherOrAdmin

audit = logging.getLogger('audit')


class IncidentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for incidents.
    - GET /api/incidents/         → public (masked data for unauthenticated)
    - POST /api/incidents/        → Dispatcher or Admin only
    - GET /api/incidents/{id}/    → public (Anti-IDOR enforced for Dispatchers)
    - PUT/PATCH /api/incidents/{id}/ → owner or Admin
    - POST /api/incidents/bulk_update_status/ → Admin only
    """
    serializer_class = IncidentSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDispatcherOrAdmin()]
        if self.action == 'bulk_update_status':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Incident.objects.prefetch_related('images').select_related('reported_by')

        if not user.is_authenticated or user.role == 'PUBLIC':
            # Public sees only active/monitoring
            return qs.filter(status__in=['ACTIVE', 'MONITORING'])

        if user.role == 'DISPATCHER':
            view_all = self.request.query_params.get('view') == 'all'
            return qs if view_all else qs.filter(reported_by=user)

        return qs  # LGU_ADMIN sees all

    def retrieve(self, request, *args, **kwargs):
        """Anti-IDOR: Dispatchers cannot access other dispatchers' incidents"""
        instance = self.get_object()
        if (request.user.is_authenticated and
                request.user.role == 'DISPATCHER' and
                instance.reported_by != request.user):
            audit.warning(
                f'API_IDOR_ATTEMPT | user={request.user.username} | '
                f'incident_id={instance.id} | ts={timezone.now()}'
            )
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        incident = serializer.save(reported_by=self.request.user)
        audit.info(
            f'API_INCIDENT_CREATED | user={self.request.user.username} | '
            f'id={incident.id} | title={incident.title} | ts={timezone.now()}'
        )

    @action(detail=False, methods=['post'], url_path='bulk_update_status')
    def bulk_update_status(self, request):
        """Bulk update incident status — LGU Admin only"""
        if not request.user.is_authenticated or request.user.role != 'LGU_ADMIN':
            audit.warning(
                f'API_UNAUTHORIZED_BULK | user={request.user.username} | ts={timezone.now()}'
            )
            return Response(
                {'detail': 'LGU Admin access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        ids = request.data.get('ids', [])
        new_status = request.data.get('status', '')
        valid_statuses = ['ACTIVE', 'MONITORING', 'RESOLVED', 'CLOSED']

        if not ids:
            return Response({'detail': 'ids list is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if new_status not in valid_statuses:
            return Response({'detail': f'status must be one of {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

        updated = Incident.objects.filter(id__in=ids).update(status=new_status)
        audit.info(
            f'API_BULK_UPDATE | user={request.user.username} | '
            f'ids={ids} | status={new_status} | updated={updated} | ts={timezone.now()}'
        )
        return Response({'updated': updated, 'new_status': new_status})


class SensorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only sensor data.
    GPS coordinates are MASKED for unauthenticated/PUBLIC users.
    """
    queryset = HazardSensor.objects.all().order_by('status', 'hazard_type')
    serializer_class = SensorSerializer
    permission_classes = [AllowAny]


class EarlyWarningViewSet(viewsets.ModelViewSet):
    """
    Early warnings API.
    - GET → public
    - POST/PUT/DELETE → Dispatcher or Admin
    """
    serializer_class = EarlyWarningSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsDispatcherOrAdmin()]

    def get_queryset(self):
        return EarlyWarning.objects.filter(is_active=True).order_by('-created_at')

    def perform_create(self, serializer):
        warning = serializer.save(issued_by=self.request.user)
        audit.info(
            f'API_WARNING_ISSUED | user={self.request.user.username} | '
            f'id={warning.id} | level={warning.alert_level} | ts={timezone.now()}'
        )

    def resolve_warning(request, pk):
        warning = get_object_or_404(EarlyWarning, pk=pk)
        warning.is_active = False
        warning.save()
        return redirect('dashboard')
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the currently authenticated user's profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_health(request):
    """Health check endpoint"""
    return Response({
        'status': 'ok',
        'system': 'LGU Disaster Early Warning System',
        'version': '1.0.0',
        'authenticated': request.user.is_authenticated,
        'timestamp': timezone.now(),
    })