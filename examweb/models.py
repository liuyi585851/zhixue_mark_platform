from pyexpat import model
from statistics import mode
from django.db import models
from django.db.models.fields import CharField

# Create your models here.
class Users(models.Model):
    username = models.CharField(max_length=128)
    status = models.CharField(max_length=128)

class Exams(models.Model):
    examname = models.CharField(max_length=1024)
    latest = models.CharField(max_length=256)

class Ukeys(models.Model):
    examname = models.CharField(max_length=1024)
    key = models.CharField(max_length=128)
    gentime = models.CharField(max_length=128)
    expiredtime = models.CharField(max_length=128)

class Recodes(models.Model):
    traceid = models.CharField(max_length=256)
    username = models.CharField(max_length=128)
    school = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    classname = models.CharField(max_length=32)
    cname = models.CharField(max_length=128)
    exam = models.CharField(max_length=128)
    time = models.CharField(max_length=128)

class Permissions(models.Model):
    username = models.CharField(max_length=128)
    view_everyone = models.BooleanField()
    developer = models.BooleanField()

class TraceIds(models.Model):
    traceid = models.CharField(max_length=128)
    username = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    time = models.CharField(max_length=128)
    message = models.CharField(max_length=256)