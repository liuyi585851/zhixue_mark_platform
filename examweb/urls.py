'''
urls.py - 路由文件
作者/anthor:liuyi585851
类型/type:后端文件-django文件-路由文件
描述/description:设置后端请求的路由
'''
from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='home'),
    path('admin/',views.admin),
    path('login/',views.login),
    path('index/',views.index),
    path('logout/',views.logout),
    path('about/',views.about),
    path('admin/index/',views.aindex),
    path('keygen/',views.keygen),
    path('update/',views.update),
    path('question/',views.question),
]

handler500 = views.page_error