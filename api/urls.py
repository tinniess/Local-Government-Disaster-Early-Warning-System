from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView, TokenVerifyView
)
from . import views

router = DefaultRouter()
router.register('incidents', views.IncidentViewSet, basename='api-incident')
router.register('sensors', views.SensorViewSet, basename='api-sensor')
router.register('warnings', views.EarlyWarningViewSet, basename='api-warning')

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # Profile
    path('me/', views.me, name='api-me'),
    # Health check
    path('health/', views.api_health, name='api-health'),
    # All resource endpoints
    path('', include(router.urls)),
]