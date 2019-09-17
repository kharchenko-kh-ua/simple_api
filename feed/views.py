"""
Feed views
"""
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import PostSerializer
from .permissions import IsNotAuthor
from .models import Post


class CreatePostView(generics.CreateAPIView):
    """
    Create post and save author
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RatePostView(generics.GenericAPIView):
    """
    Common likes view
    """
    permission_classes = (IsAuthenticated, IsNotAuthor)
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    action = None

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        getattr(post, self.action)(request.user.id)
        return Response(status=status.HTTP_200_OK)


class LikePostView(RatePostView):
    """
    Increment likes
    """
    action = 'like'


class UnlikePostView(RatePostView):
    """
    Decrement likes
    """
    action = 'unlike'
