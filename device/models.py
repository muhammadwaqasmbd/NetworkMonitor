from django.db import models


# Create your models here.
class Device(models.Model):
    protocol = models.CharField(max_length=50, blank=False, default='')
    host = models.CharField(max_length=200, blank=False, default='')
    source_ip = models.CharField(max_length=200, blank=False, default='')
    source_port = models.CharField(max_length=50, blank=False, default='')
    source_mac = models.CharField(max_length=200, blank=False, default='')
    destination_ip = models.CharField(max_length=200, blank=False, default='')
    destination_port = models.CharField(max_length=50, blank=False, default='')
    destination_mac = models.CharField(max_length=200, blank=False, default='')
    destination_country = models.CharField(max_length=200, blank=False, default='')
    packets_length = models.CharField(max_length=200, blank=False, default='')
    class Meta:
        db_table = "device"