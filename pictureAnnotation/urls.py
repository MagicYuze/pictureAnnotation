"""pictureAnnotation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from pictureAnnotationSystem import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test/', views.showTest),
    path('cut_pic/', views.cut_pic),
    path('get_url/', views.get_url),
    path('get_pics/', views.get_pics),
    path('get_pic_infos/', views.get_pic_infos),
    path('file_upload/', views.file_upload),
    path('del_annotation/', views.del_annotation),
    path('del_picture/', views.del_picture),
    path('update_annotation_pic/', views.cut_pic),
    path('update_annotation_text/', views.update_annotation_text),
    url(r'^$', views.showIndex),
]
