from rest_framework.permissions import BasePermission
from datetime import datetime


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user and request.user.is_staff


class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsInGroup(BasePermission):
    """
    Grants access to users in a specific group.
    """

    group_name = "editors"

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.groups.filter(name=self.group_name).exists()
        )


class AccessDuringBusinessHours(BasePermission):
    """
    Grant access only between 9 AM to 5 PM.
    """

    def has_permission(self, request, view):
        current_hour = datetime.now().hour
        return 9 <= current_hour < 17
