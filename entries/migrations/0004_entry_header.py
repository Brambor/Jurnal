# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-27 11:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0003_entry_place'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='header',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
