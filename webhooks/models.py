from django.db import models

class Payload(models.Model):
    source = models.CharField(max_length=300, blank=True, null=True)
    event = models.CharField(max_length=300, blank=True, null=True)
    payload = models.JSONField(blank=True, null=True,)
    last_update_timestamp = models.DateTimeField(auto_now=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Source: {self.source}"
