# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import json
import math
import os
import tempfile
import time

from zipfile import ZipFile

import arrow
import numpy

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint


SPLIT_SIZE = 10000

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Accelerometer Sensor'

def compile_frequency_visualization(identifier, points, folder): # pylint: disable=unused-argument,too-many-locals
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

    while start < now: # pylint: disable=too-many-nested-blocks
        timestamp = str(time.mktime(start.timetuple()))

        keys.append(timestamp)

        timestamp_counts[timestamp] = 0

        while point is not None and point.created < end and point_index < (point_count - 1):
            properties = point.fetch_properties()

            if 'sensor_data' in properties:
                try:
                    for timestamp in properties['sensor_data']['observed']:
                        timestamp = timestamp / (1000 * 1000 * 1000)

                        for key in keys:
                            key_end = float(key) + 600

                            if timestamp >= float(key) and timestamp <= key_end:
                                timestamp_counts[key] += 1
                except KeyError:
                    pass
                except TypeError:
                    pass

            point_index += 1

            point = points[point_index]

        start = end
        end = start + datetime.timedelta(seconds=600)

    timestamp_counts['keys'] = keys

    with open(folder + '/timestamp-counts.json', 'w') as outfile:
        json.dump(timestamp_counts, outfile, indent=2)

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    context = {}

    values = []

    now = timezone.now()

    now = now.replace(second=0, microsecond=0)

    remainder = now.minute % 10

    now = now.replace(minute=(now.minute - remainder))

    start = now - datetime.timedelta(days=2)

    points = points.filter(created__gte=start)

    for point in points.order_by('-created'):
        properties = point.fetch_properties()

        if 'sensor_data' in properties:
            try:
                value = {}

                value['ts'] = properties['passive-data-metadata']['timestamp']
                value['x_mean'] = numpy.mean(properties['sensor_data']['x'])
                value['y_mean'] = numpy.mean(properties['sensor_data']['y'])
                value['z_mean'] = numpy.mean(properties['sensor_data']['z'])

                value['x_std'] = numpy.std(properties['sensor_data']['x'])
                value['y_std'] = numpy.std(properties['sensor_data']['y'])
                value['z_std'] = numpy.std(properties['sensor_data']['z'])

                values.insert(0, value)
            except KeyError:
                pass
            except TypeError:
                pass

    context['values'] = values

    context['start'] = time.mktime(start.timetuple())
    context['end'] = time.mktime(now.timetuple())

    with open(folder + '/accelerometer.json', 'w') as outfile:
        json.dump(context, outfile, indent=2)

    compile_frequency_visualization(identifier, points, folder)


def visualization(source, generator): # pylint: disable=unused-argument
    context = {}

    filename = settings.MEDIA_ROOT + 'pdk_visualizations/' + source.identifier + '/pdk-sensor-accelerometer/accelerometer.json'

    with open(filename) as infile:
        data = json.load(infile)
        context['viz_data'] = data

    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-sensor-accelerometer/timestamp-counts.json'

    try:
        with open(filename) as infile:
            hz_data = json.load(infile)

            context['hz_data'] = hz_data
    except IOError:
        context['hz_data'] = {}

    return render_to_string('generators/pdk_sensor_accelerometer_template.html', context)


def data_table(source, generator): # pylint: disable=unused-argument
    filename = settings.MEDIA_ROOT + 'pdk_visualizations/' + source.identifier + '/pdk-sensor-accelerometer/accelerometer.json'

    with open(filename) as infile:
        data = json.load(infile)

        return render_to_string('generators/pdk_sensor_accelerometer_table_template.html', data)

    return None

def compile_report(generator, sources): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(now.microsecond / 1e6) + '.zip'

    with ZipFile(filename, 'w', allowZip64=True) as export_file:
        for source in sources:
            points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created')

            points_count = float(points.count())

            splits = int(math.ceil(points_count / SPLIT_SIZE))

            for split_index in range(0, splits):
                identifier = slugify(generator + '__' + source)

                if splits > 1:
                    identifier += '__' + str(split_index)

                secondary_filename = tempfile.gettempdir() + '/' + identifier + '.txt'

                with open(secondary_filename, 'w') as outfile:
                    writer = csv.writer(outfile, delimiter='\t')

                    columns = [
                        'Source',
                        'Created Timestamp',
                        'Created Date',
                        'Recorded Timestamp',
                        'Recorded Date',
                        'Raw Timestamp',
                        'Normalized Timestamp',
                        'X',
                        'Y',
                        'Z',
                        'Accuracy'
                    ]

                    writer.writerow(columns)

                    index = split_index * SPLIT_SIZE

                    while index < (split_index + 1) * SPLIT_SIZE and index < points_count:
                        for point in points[index:(index + 500)]:
                            properties = point.fetch_properties()

                            if 'observed' in properties['sensor_data']:
                                for i in range(0, len(properties['sensor_data']['observed'])):
                                    row = []

                                    row.append(point.source)
                                    row.append(calendar.timegm(point.created.utctimetuple()))
                                    row.append(point.created.isoformat())

                                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                                    row.append(point.recorded.isoformat())

                                    try:
                                        row.append(properties['sensor_data']['raw_timestamp'][i])
                                    except IndexError:
                                        row.append('')

                                    try:
                                        row.append(properties['sensor_data']['observed'][i])
                                    except IndexError:
                                        row.append('')

                                    try:
                                        row.append(properties['sensor_data']['x'][i])
                                    except IndexError:
                                        row.append('')

                                    try:
                                        row.append(properties['sensor_data']['y'][i])
                                    except IndexError:
                                        row.append('')

                                    try:
                                        row.append(properties['sensor_data']['z'][i])
                                    except IndexError:
                                        row.append('')

                                    try:
                                        row.append(properties['sensor_data']['accuracy'][i])
                                    except IndexError:
                                        row.append('')

                                    writer.writerow(row)

                        index += 500

                source_name = source

                if splits > 1:
                    source_name += '__' + str(split_index)

                export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source_name) + '.txt')

                os.remove(secondary_filename)

    return filename
