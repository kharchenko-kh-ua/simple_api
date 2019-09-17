"""
Feed models
"""
from django.conf import settings
from django.db import models


class Post(models.Model):
    """"
    Post model
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author.email}: {self.message[:100]}'

    def like(self, user_id):
        Like.objects.get_or_create(user_id=user_id, post=self)

    def unlike(self, user_id):
        Like.objects.filter(user_id=user_id, post=self).delete()


class Like(models.Model):
    """
    Save user who liked post. User can like post only once.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes',
                             on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'post')
