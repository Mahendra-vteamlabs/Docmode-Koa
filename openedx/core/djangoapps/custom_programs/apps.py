# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class CustomProgramsManagementConfig(AppConfig):
    name = "openedx.core.djangoapps.custom_programs"

    def ready(self):
        # Import signals to activate signal handler which invalidates
        # the CourseOverview cache every time a course is published.
        from . import signals  # pylint: disable=unused-variable
