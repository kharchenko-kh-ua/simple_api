"""
Permissions
"""
from rest_framework.permissions import BasePermission


class IsNotAuthor(BasePermission):
    """
    User is not author
    """
    def has_object_permission(self, request, view, obj):
        return request.user != obj.author
