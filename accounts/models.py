from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class UserProfile(models.Model):
    live = 1
    delete = 0
    user_status = ((live, 'Live'), (delete, 'Delete'))

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    name = models.CharField(max_length=120, null=True)
    phone = models.CharField(max_length=120, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_status = models.IntegerField(choices=user_status, default=live)

    def __str__(self):
        return self.user.username