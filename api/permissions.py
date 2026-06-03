from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsLGUAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_lgu_admin()

class IsDispatcherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_lgu_admin() or request.user.is_dispatcher()
        )

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_lgu_admin():
            return True
        return obj.reported_by == request.user