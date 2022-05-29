'''
models.py - 后端数据表文件
作者/anthor:liuyi585851
类型/type:后端文件-django文件-数据表文件
描述/description:设置数据库对应表及字段
使用方法/usage:
Users --> 用户信息表单
    username --> 用户名 文本型 128
    status --> 用户权限 文本型 128
Exams --> 已缓存考试信息表单
    examname --> 考试名称 文本型 1024
    latest --> 最后刷新时间 文本型 256
Ukeys --> 考试刷新密钥表单
    examname --> 考试名称 文本型 1024
    key --> 密钥串 文本型 128
    gentime --> 生成时间 文本型 128
    expiredtime --> 过期时间 文本型 128
Recodes --> 查询记录表单
    traceid --> 记录id 文本型 256
    username --> 查询人id 文本型 128
    school --> 查询人学校 文本型 128
    name --> 查询人姓名 文本型 128
    classname --> 查询人班级 文本型 32
    cname --> 被查询人姓名 文本型 128
    exam --> 考试名称 文本型 128
    time --> 查询时间 文本型 128
Permissions --> 用户权限表单
    username --> 用户名 文本型 128
    view_everyone --> 是否能查询他人成绩 布尔型
    developer --> 是否是开发者 布尔型
TraceIds --> 错误记录表单
    traceid --> 错误记录id 文本型 128
    username --> 登录id 文本型 128
    password --> 登录密码 文本型 128
    time --> 登录时间 文本型 128
    message --> 错误信息 文本型 256
'''
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