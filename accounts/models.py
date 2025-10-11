
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    date_of_birth = models.DateField(null=True, blank=True)

    ROLE_CREATOR = 'creator'
    ROLE_ADMIN = 'admin'
    ROLE_MODER = 'moder'
    ROLE_HELPER = 'helper'
    ROLE_CHOICES = [
        (ROLE_CREATOR, 'Создатель'),
        (ROLE_ADMIN, 'Админ'),
        (ROLE_MODER, 'Модер'),
        (ROLE_HELPER, 'Хелпер'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_HELPER)

    def __str__(self):
        return self.username

from django.utils import timezone
import random
from datetime import timedelta

class PasswordResetCode(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='reset_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=30)

    @classmethod
    def create_for_user(cls, user):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(user=user, code=code)

    def mark_used(self):
        self.used = True
        self.save()
