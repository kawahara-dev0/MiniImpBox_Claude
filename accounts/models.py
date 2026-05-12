from django.db import models


class AdminLoginLog(models.Model):
    email        = models.CharField(max_length=254)
    success      = models.BooleanField()
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-attempted_at']
