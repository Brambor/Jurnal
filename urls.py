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
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin

import settings

from entries import views

urlpatterns = [
	path('admin/', admin.site.urls),
    path('', views.index),
    path('readAt/<int:pk>', views.add_read_at),
    path('all', views.get_all_entries),
    path('list', views.list_headers),
    path('entry/<int:pk>', views.entry),
    path('change_pks', views.change_pks),
    path('change_pks_diff', views.change_pks_diff),
    path('sync_connect', views.sync_connect),
    path('sync_diff', views.sync_diff),
    path('sync_process_diff', views.sync_process_diff),
    path('sync_get_model/<model_name>', views.sync_get_model),
    path('sync_update', views.sync_update),
    path('graph', views.GraphView.as_view()),
	path('<int:year>/<int:month>/<int:day>/', views.greetings, name='jurnal'),
#	url(r'^', greetings),  # this would break media
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
