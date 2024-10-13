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
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView

import settings

from entries import views

urlpatterns = [
	url(r'^admin/', admin.site.urls),
    url(r'^$', views.index),
    url(r'^readAt/(?P<pk>[0-9]+)$', views.add_read_at),
    url(r'^all$', views.get_all_entries),
    url(r'^list$', views.list_headers),
    url(r'^entry/(?P<pk>[0-9]+)$', views.entry),
    url(r'^sync_page$', views.sync_page),
    url(r'^sync$', views.sync_request_send),
    url(r'^sync_recieve$', views.sync_request_recieve),
    url(r'^sync_complete$', views.sync_request_complete),
    url(r'^graph$', views.GraphView.as_view()),
	url(r'^(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$', views.greetings, name='jurnal'),
#	url(r'^', greetings),  # this would break media
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
