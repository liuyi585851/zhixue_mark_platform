"""exam URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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