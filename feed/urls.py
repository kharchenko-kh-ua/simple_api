"""
Feed urls
"""
from django.urls import path
from .views import CreatePostView, LikePostView, UnlikePostView


urlpatterns = [
    path('post/create/', CreatePostView.as_view()),
    path('post/<int:pk>/like/', LikePostView.as_view()),
    path('post/<int:pk>/unlike/', UnlikePostView.as_view()),
]
