"""illustriousPeopleProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from ipersApp import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',views.home , name = 'home'),
    url(r'^people/', views.people, name='people'),
    url(r'^person/', views.person, name='person'),
    url(r'^works/', views.works, name='works'),
    url(r'^work/', views.work, name='work'),
    url(r'^search_result/', views.search_result, name='search_result'),
    url(r'^work_search_result/', views.work_search_result, name='work_search_result'),
]
