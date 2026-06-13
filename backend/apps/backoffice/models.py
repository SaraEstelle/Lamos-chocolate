from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from apps.common.constants import AdminRoleChoices


class AdminUser(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, blank=True, default="")
    last_name = models.CharField(max_length=100, blank=True, default="")
    role = models.CharField(
        max_length=20,
        choices=AdminRoleChoices.choices,
        default=AdminRoleChoices.ADMIN,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "admin_users"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)
