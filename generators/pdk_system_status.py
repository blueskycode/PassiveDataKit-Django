# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import json
import os
import tempfile
import time

from zipfile import ZipFile

import arrow

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint

def generator_name(identifier): # pylint: disable=unused-argument
    return 'System Status'

def visualization(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    start = timezone.now() - datetime.timedelta(days=7)

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gte=start).order_by('-created')

    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-system-status/timestamp-counts.json'

    try:
        with open(filename) as infile:
            hz_data = json.load(infile)

            context['hz_data'] = hz_data
    except IOError:
        context['hz_data'] = {}

    return render_to_string('generators/pdk_device_system_status_template.html', context)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    start = timezone.now() - datetime.timedelta(days=7)

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gte=start).order_by('-created')

    return render_to_string('generators/pdk_device_system_status_table_template.html', context)

def compile_report(generator, sources): # pylint: disable=too-many-locals
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(now.microsecond / 1e6) + '.zip'

    with ZipFile(filename, 'w') as export_file:
        for source in sources:
            identifier = slugify(generator + '__' + source)

            secondary_filename = tempfile.gettempdir() + '/' + identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    'Source',
                    'Created Timestamp',
                    'Created Date',
                    'Recorded Timestamp',
                    'Recorded Date',
                    'Available Storage',
                    'Other Storage',
                    'App Storage',
                    'Total Storage',
                    'App Runtime',
                ]

                writer.writerow(columns)

                points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created')

                for point in points:
                    properties = point.fetch_properties()

                    row = []

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(point.created.isoformat())

                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(point.recorded.isoformat())

                    row.append(properties['storage_available'])
                    row.append(properties['storage_other'])
                    row.append(properties['storage_app'])
                    row.append(properties['storage_total'])

                    if 'runtime' in properties:
                        row.append(properties['runtime'])
                    else:
                        row.append(None)

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source) + '.txt')

            os.remove(secondary_filename)

    return filename

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    now = timezone.now()

    now = now.replace(second=0, microsecond=0)

    remainder = now.minute % 10

    now = now.replace(minute=(now.minute - remainder))

    start = now - datetime.timedelta(days=2)

    points = points.filter(created__lte=now, created__gte=start).order_by('created')

    end = start + datetime.timedelta(seconds=600)
    point_index = 0
    point_count = points.count()

    point = None

    if point_count > 0:
        point = points[point_index]

    timestamp_counts = {}

    keys = []

    while start < now:
        timestamp = str(time.mktime(start.timetuple()))

        keys.append(timestamp)

        timestamp_counts[timestamp] = 0

        while point is not None and point.created < end and point_index < (point_count - 1):
            timestamp_counts[timestamp] += 1

            point_index += 1

            point = points[point_index]

        start = end
        end = start + datetime.timedelta(seconds=600)

    timestamp_counts['keys'] = keys

    with open(folder + '/timestamp-counts.json', 'w') as outfile:
        json.dump(timestamp_counts, outfile, indent=2)
