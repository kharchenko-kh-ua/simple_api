"""
Common views
"""
from rest_framework import generics, permissions

from .serializers import CreateUserSerializer


class SignUpView(generics.CreateAPIView):
    """
    Registration
    """
    serializer_class = CreateUserSerializer
    permission_classes = (~permissions.IsAuthenticated,)
