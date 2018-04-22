"""Jurnal URL Configuration

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
from django.views.generic import RedirectView

import settings

from entries.views import GraphView, greetings, get_all_entries

urlpatterns = [
	url(r'^admin/', admin.site.urls),
    url(r'^$', get_all_entries),
    url(r'^graph$', GraphView.as_view()),
	url(r'^(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$', greetings, name='jurnal'),
	url(r'^', greetings),
]