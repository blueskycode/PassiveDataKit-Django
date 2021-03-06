# pylint: disable=line-too-long, no-member

import datetime
import importlib
import traceback

import arrow

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataSourceAlert

register = template.Library()

@register.tag(name="sources_table")
def sources_table(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, query = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return SourcesTableNode(query)

class SourcesTableNode(template.Node):
    def __init__(self, query):
        self.query = template.Variable(query)

    def render(self, context):
        query = self.query.resolve(context)

        context['sources'] = query

        return render_to_string('tag_sources_table.html', context.flatten())


@register.tag(name="latest_point")
def latest_point(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" %
                                           token.contents.split()[0])

    return LatestPointNode(source)

class LatestPointNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['latest_point'] = source.latest_point()

        return render_to_string('tag_latest_point.html', context.flatten())


@register.tag(name="point_count")
def point_count(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return PointCountNode(source)

class PointCountNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        return source.point_count()


@register.tag(name="point_hz")
def point_hz(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return PointHzNode(source)

class PointHzNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        frequency = source.point_frequency()

        if frequency is None:
            frequency = 0

        value = "{:10.3f}".format(frequency) + " Hz"

        if frequency < 1.0:
            value = "{:10.3f}".format(frequency * 1000) + " mHz"

        tooltip = "{:10.3f}".format(frequency) + " samples per second"

        if frequency < 1.0:
            frequency *= 60

            if frequency > 1.0:
                tooltip = "{:10.3f}".format(frequency) + " samples per minute"
            else:
                frequency *= 60

                if frequency > 1.0:
                    tooltip = "{:10.3f}".format(frequency) + " samples per hour"
                else:
                    frequency *= 24

                    if frequency > 1.0:
                        tooltip = "{:10.3f}".format(frequency) + " samples per day"
                    else:
                        frequency *= 7

                        tooltip = "{:10.3f}".format(frequency) + " samples per week"

        context['value'] = value
        context['tooltip'] = tooltip

        return render_to_string('tag_point_hz.html', context.flatten())

@register.tag(name="to_hz")
def to_hz(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, frequency = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return ToHzNode(frequency)

class ToHzNode(template.Node):
    def __init__(self, frequency):
        self.frequency = template.Variable(frequency)

    def render(self, context):
        frequency = self.frequency.resolve(context)

        value = "{:10.3f}".format(frequency) + " Hz"

        if frequency < 1.0:
            value = "{:10.3f}".format(frequency * 1000) + " mHz"

        tooltip = "{:10.3f}".format(frequency) + " samples per second"

        if frequency < 1.0:
            frequency *= 60

            if frequency > 1.0:
                tooltip = "{:10.3f}".format(frequency) + " samples per minute"
            else:
                frequency *= 60

                if frequency > 1.0:
                    tooltip = "{:10.3f}".format(frequency) + " samples per hour"
                else:
                    frequency *= 24

                    if frequency > 1.0:
                        tooltip = "{:10.3f}".format(frequency) + " samples per day"
                    else:
                        frequency *= 7

                        tooltip = "{:10.3f}".format(frequency) + " samples per week"

        context['value'] = value
        context['tooltip'] = tooltip

        return render_to_string('tag_point_hz.html', context.flatten())

@register.tag(name="date_ago")
def date_ago(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, date_obj = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return DateAgoNode(date_obj)

class DateAgoNode(template.Node):
    def __init__(self, date_obj):
        self.date_obj = template.Variable(date_obj)

    def render(self, context):
        date_obj = self.date_obj.resolve(context)

        if date_obj is None:
            return 'None'

        now = timezone.now()

        diff = arrow.get(now.isoformat()).datetime - arrow.get(date_obj.isoformat()).datetime

        ago_str = 'Unknown'

        if diff.days > 0:
            ago_str = str(diff.days) + 'd'
        else:
            minutes = diff.seconds / 60

            if minutes >= 60:
                ago_str = str(minutes / 60) + 'h'
            else:
                ago_str = str(minutes) + 'm'

        context['ago'] = ago_str
        context['date'] = date_obj

        return render_to_string('tag_date_ago.html', context.flatten())


@register.tag(name="human_duration")
def tag_human_duration(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, seconds_obj = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return HumanDurationNode(seconds_obj)

class HumanDurationNode(template.Node):
    def __init__(self, seconds_obj):
        self.seconds_obj = template.Variable(seconds_obj)

    def render(self, context):
        seconds_obj = self.seconds_obj.resolve(context)

        if seconds_obj is None:
            return ''

        ago_str = str(seconds_obj) + 's'

        if seconds_obj > (24.0 * 60 * 60):
            ago_str = "{0:.2f}".format(seconds_obj / (24.0 * 60 * 60)) + 'd'
        elif seconds_obj > (60.0 * 60):
            ago_str = "{0:.2f}".format(seconds_obj / (60.0 * 60)) + 'h'
        elif seconds_obj > 60.0:
            ago_str = "{0:.2f}".format(seconds_obj / 60.0) + 'm'

        context['human_duration'] = ago_str
        context['seconds'] = seconds_obj

        return render_to_string('tag_human_duration.html', context.flatten())


@register.tag(name="generators_table")
def generators_table(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return GeneratorsTableNode(source)

class GeneratorsTableNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['source'] = source

        return render_to_string('tag_generators_table.html', context.flatten())


@register.tag(name="generator_label")
def generator_label(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, generator_id = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return GeneratorLabelNode(generator_id)

class GeneratorLabelNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['source'] = source

        return render_to_string('tag_generators_table.html', context.flatten())


@register.tag(name="system_alerts_table")
def system_alerts_table(parser, token): # pylint: disable=unused-argument
    return SystemAlertsTableNode()

class SystemAlertsTableNode(template.Node):
    def __init__(self):
        pass

    def render(self, context):

        context['alerts'] = DataSourceAlert.objects.filter(active=True)

        return render_to_string('tag_system_alerts_table.html', context.flatten())

@register.tag(name="system_alerts_badge")
def system_alerts_badge(parser, token): # pylint: disable=unused-argument
    return SystemAlertsCountBadge()

class SystemAlertsCountBadge(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        count = DataSourceAlert.objects.filter(active=True).count()

        if count > 0:
            return '<span class="badge pull-right">' + str(count) + '</span>'

        return ''

@register.tag(name="source_alerts_table")
def source_alerts_table(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return SourceAlertsTableNode(source)

class SourceAlertsTableNode(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        context['alerts'] = DataSourceAlert.objects.filter(active=True, data_source=source)

        return render_to_string('tag_source_alerts_table.html', context.flatten())

@register.tag(name="source_alerts_badge")
def source_alerts_badge(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])
    return SourceAlertsCountBadge(source)

class SourceAlertsCountBadge(template.Node):
    def __init__(self, source):
        self.source = template.Variable(source)

    def render(self, context):
        source = self.source.resolve(context)

        count = DataSourceAlert.objects.filter(active=True, data_source=source).count()

        if count > 0:
            return '<span class="badge pull-right">' + str(count) + '</span>'

        return ''

@register.tag(name="generator_name")
def generator_name(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, generator = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])
    return GeneratorName(generator)

class GeneratorName(template.Node):
    def __init__(self, generator):
        self.generator = template.Variable(generator)

    def render(self, context):
        generator = self.generator.resolve(context)

        for app in settings.INSTALLED_APPS:
            try:
                generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package=app)

                output = generator_module.generator_name(generator)

                if output is not None:
                    return output
            except ImportError:
                pass
#                traceback.print_exc()
            except AttributeError:
                pass
#                traceback.print_exc()

        return generator

@register.filter("to_datetime")
def to_datetime(value):
    if value is None or value == '':
        return None

    return arrow.get(value).datetime


@register.tag(name="hour_minute_to_time")
def hour_minute_to_time(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, hour, minute = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % \
                                           token.contents.split()[0])

    return HourMinuteTimeNode(hour, minute)

class HourMinuteTimeNode(template.Node):
    def __init__(self, hour, minute):
        self.hour = template.Variable(hour)
        self.minute = template.Variable(minute)

    def render(self, context):
        hour = int(self.hour.resolve(context))
        minute = int(self.minute.resolve(context))

        return datetime.time(hour, minute, 0, 0)


@register.tag(name="points_visualization")
def points_visualization(parser, token): # pylint: disable=unused-argument
    try:
        tag_name, source, generator = token.split_contents() # pylint: disable=unused-variable
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires 2 arguments" % \
                                           token.contents.split()[0])

    return PointsVisualizationNode(source, generator)

class PointsVisualizationNode(template.Node):
    def __init__(self, source, generator):
        self.source = template.Variable(source)
        self.generator = template.Variable(generator)

    def render(self, context):
        source = self.source.resolve(context)
        generator = self.generator.resolve(context)

        visualization_html = None

        for app in settings.INSTALLED_APPS:
            if visualization_html is None:
                try:
                    pdk_api = importlib.import_module(app + '.pdk_api')

                    visualization_html = pdk_api.visualization(source, generator)
                except ImportError:
                    traceback.print_exc()
                except AttributeError:
                    traceback.print_exc()

        return visualization_html

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter("to_gb")
def to_gb(value):
    value = (value / (1024.0 * 1024.0 * 1024.0))

    if value > 1:
        return '%.3f GB' %  value

    value = value * 1024

    return '%.3f MB' %  value
