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

from entries.views import GraphView, greetings, get_all_entries, list_headers, entry, entry_history, index, sync_request_send, sync_request_recieve

urlpatterns = [
	url(r'^admin/', admin.site.urls),
    url(r'^$', index),
    url(r'^all$', get_all_entries),
    url(r'^list$', list_headers),
    url(r'^entry/(?P<pk>[0-9]+)$', entry),
    url(r'^history/(?P<pk>[0-9]+)$', entry_history),
    url(r'^sync$', sync_request_send),
    url(r'^sync_recieve$', sync_request_recieve),
    url(r'^graph$', GraphView.as_view()),
	url(r'^(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$', greetings, name='jurnal'),
#	url(r'^', greetings),  # this would break media
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
