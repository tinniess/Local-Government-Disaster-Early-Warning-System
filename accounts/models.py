from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_LGU_ADMIN = 'LGU_ADMIN'
    ROLE_DISPATCHER = 'DISPATCHER'
    ROLE_PUBLIC = 'PUBLIC'

    ROLE_CHOICES = [
        (ROLE_LGU_ADMIN, 'LGU Admin'),
        (ROLE_DISPATCHER, 'Dispatcher'),
        (ROLE_PUBLIC, 'Public Viewer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PUBLIC)
    municipality = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def is_lgu_admin(self):
        return self.role == self.ROLE_LGU_ADMIN

    def is_dispatcher(self):
        return self.role == self.ROLE_DISPATCHER

    def is_public(self):
        return self.role == self.ROLE_PUBLIC

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'