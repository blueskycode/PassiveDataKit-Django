# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-19 22:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0011_auto_20160319_2158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportjob',
            name='report',
            field=models.FileField(blank=True, null=True, upload_to='pdk_reports'),
        ),
    ]
