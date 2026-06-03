from rest_framework import serializers
from incidents.models import Incident, HazardSensor, EarlyWarning, HazardImage
from accounts.models import User


class HazardImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HazardImage
        fields = ['id', 'image', 'caption', 'uploaded_at']


class SensorSerializer(serializers.ModelSerializer):
    hazard_type_display = serializers.CharField(source='get_hazard_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = HazardSensor
        fields = ['id', 'name', 'hazard_type', 'hazard_type_display', 'status',
                  'status_display', 'latitude', 'longitude', 'municipality',
                  'last_reading', 'unit', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        # FIELD-LEVEL MASKING: hide precise GPS from unauthenticated or PUBLIC users
        if not request or not request.user.is_authenticated or request.user.role == 'PUBLIC':
            data['latitude'] = '*** MASKED ***'
            data['longitude'] = '*** MASKED ***'
        return data


class IncidentSerializer(serializers.ModelSerializer):
    images = HazardImageSerializer(many=True, read_only=True)
    reported_by_username = serializers.SerializerMethodField()
    dispatcher_contact = serializers.SerializerMethodField()
    location_details = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    hazard_type_display = serializers.CharField(source='get_hazard_type_display', read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'hazard_type', 'hazard_type_display',
            'status', 'status_display', 'severity', 'severity_display',
            'municipality', 'location_details', 'affected_population',
            'reported_by_username', 'dispatcher_contact',
            'created_at', 'updated_at', 'images'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_reported_by_username(self, obj):
        return obj.reported_by.username if obj.reported_by else None

    def get_dispatcher_contact(self, obj):
        """FIELD-LEVEL MASKING: hide dispatcher contact from public/unauthenticated"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.role == 'PUBLIC':
            return '*** MASKED — login required ***'
        if obj.reported_by:
            return obj.reported_by.contact_number or 'N/A'
        return 'N/A'

    def get_location_details(self, obj):
        """FIELD-LEVEL MASKING: hide precise location from unauthenticated"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return '*** MASKED — login required ***'
        return obj.location_details


class EarlyWarningSerializer(serializers.ModelSerializer):
    alert_level_display = serializers.CharField(source='get_alert_level_display', read_only=True)
    issued_by_username = serializers.SerializerMethodField()

    class Meta:
        model = EarlyWarning
        fields = [
            'id', 'title', 'message', 'alert_level', 'alert_level_display',
            'municipality', 'is_active', 'issued_by_username',
            'created_at', 'expires_at'
        ]

    def get_issued_by_username(self, obj):
        return obj.issued_by.username if obj.issued_by else None


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'role_display',
                  'municipality', 'first_name', 'last_name']
        read_only_fields = ['id', 'role']