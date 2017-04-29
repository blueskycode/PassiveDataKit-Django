# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-24 22:39
# pylint: skip-file

from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('passive_data_kit', '0004_auto_20160224_2218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasource',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sources', to='passive_data_kit.DataSourceGroup'),
        ),
    ]
