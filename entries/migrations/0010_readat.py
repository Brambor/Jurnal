# Generated by Django 3.2.12 on 2022-02-24 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0009_auto_20210302_0238'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReadAt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='entries.entry')),
            ],
        ),
    ]
