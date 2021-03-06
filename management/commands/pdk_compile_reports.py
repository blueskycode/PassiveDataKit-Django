# -*- coding: utf-8 -*-
# pylint: disable=no-member,line-too-long

import datetime
import importlib
import json
import os
import tempfile
import zipfile

import zipstream

from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from ...decorators import handle_lock
from ...models import DataPoint, ReportJob, ReportJobBatchRequest, install_supports_jsonfield

class Command(BaseCommand):
    help = 'Compiles data reports requested by end users.'

    def add_arguments(self, parser):
        pass
#        parser.add_argument('--delete',
#            action='store_true',
#            dest='delete',
#            default=False,
#            help='Delete data bundles after processing')
#
#        parser.add_argument('--count',
#            type=int,
#            dest='bundle_count',
#            default=100,
#            help='Number of bundles to process in a single run')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        os.umask(000)

        report = ReportJob.objects.filter(started=None, completed=None)\
                                  .order_by('requested', 'pk')\
                                  .first()

        if report is not None:
            report.started = timezone.now()
            report.save()

            parameters = {}

            if install_supports_jsonfield():
                parameters = report.parameters
            else:
                parameters = json.loads(report.parameters)

            sources = parameters['sources']
            generators = parameters['generators']

            raw_json = False

            if ('raw_data' in parameters) and parameters['raw_data'] is True:
                raw_json = True

            filename = tempfile.gettempdir() + '/pdk_export_final_' + str(report.pk) + '_' + report.started.date().isoformat() + '.zip'

            with open(filename, 'wb') as final_output_file:
                with zipstream.ZipFile(mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as export_stream: # pylint: disable=line-too-long
                    to_delete = []

                    for generator in generators: # pylint: disable=too-many-nested-blocks
                        if raw_json:
                            for source in sources:
                                first = DataPoint.objects.filter(source=source, generator_identifier=generator).first() # pylint: disable=line-too-long
                                last = DataPoint.objects.filter(source=source, generator_identifier=generator).last() # pylint: disable=line-too-long

                                if first is not None:
                                    first_create = first.created
                                    last_create = last.created

                                    start = datetime.datetime(first_create.year, \
                                                              first_create.month, \
                                                              first_create.day, \
                                                              0, \
                                                              0, \
                                                              0, \
                                                              0, \
                                                              first_create.tzinfo)

                                    end = datetime.datetime(last_create.year, \
                                                            last_create.month, \
                                                            last_create.day, \
                                                            0, \
                                                            0, \
                                                            0, \
                                                            0, \
                                                            first_create.tzinfo) + \
                                          datetime.timedelta(days=1)

                                    while start <= end:
                                        day_end = start + datetime.timedelta(days=1)

                                        day_filename = source + '__' + generator + '__' + \
                                                       start.date().isoformat() + '.json'

                                        points = DataPoint.objects.filter(source=source, generator_identifier=generator, created__gte=start, created__lt=day_end).order_by('created') # pylint: disable=line-too-long

                                        out_points = []

                                        for point in points:
                                            out_points.append(point.properties)

                                        if out_points:
                                            export_stream.writestr(day_filename, unicode(json.dumps(out_points, indent=2)).encode("utf-8")) # pylint: disable=line-too-long

                                        start = day_end
                        else:
                            output_file = None

                            for app in settings.INSTALLED_APPS:
                                if output_file is None:
                                    try:
                                        pdk_api = importlib.import_module(app + '.pdk_api')

                                        output_file = pdk_api.compile_report(generator, sources)

                                        if output_file is not None:
                                            if output_file.lower().endswith('.zip'):
                                                with zipfile.ZipFile(output_file, 'r') as source_file:
                                                    for name in source_file.namelist():
                                                        data_file = source_file.open(name)

                                                        export_stream.write_iter(name, data_file, compress_type=zipfile.ZIP_DEFLATED)
                                            else:
                                                name = os.path.basename(os.path.normpath(output_file))

                                                export_stream.write(output_file, name, compress_type=zipfile.ZIP_DEFLATED)

                                            to_delete.append(output_file)
                                    except ImportError:
                                        output_file = None
                                    except AttributeError:
                                        output_file = None

                    for data in export_stream:
                        final_output_file.write(data)

                    for output_file in to_delete:
                        os.remove(output_file)

            report.report.save(filename.split('/')[-1], File(open(filename, 'r')))
            report.completed = timezone.now()
            report.save()

            os.remove(filename)

            subject = render_to_string('pdk_report_subject.txt', {
                'report': report,
                'url': settings.SITE_URL
            })

            message = render_to_string('pdk_report_message.txt', {
                'report': report,
                'url': settings.SITE_URL
            })

            tokens = settings.SITE_URL.split('/')
            host = ''

            while tokens and tokens[-1] == '':
                tokens.pop()

            if tokens:
                host = tokens[-1]

            send_mail(subject, \
                      message, \
                      'Petey Kay <noreply@' + host + '>', \
                      [report.requester.email], \
                      fail_silently=False)
        else:
            request = ReportJobBatchRequest.objects.filter(started=None, completed=None)\
                          .order_by('requested', 'pk')\
                          .first()

            if request is not None:
                request.process()
