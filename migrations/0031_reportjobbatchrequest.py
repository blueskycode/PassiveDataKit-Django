# pylint: skip-file

# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-07 16:31
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('passive_data_kit', '0030_auto_20170907_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportJobBatchRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested', models.DateTimeField(db_index=True)),
                ('completed', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('parameters', django.contrib.postgres.fields.jsonb.JSONField()),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
