# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import markupsafe
from config_models.models import ConfigurationModel
from django.contrib.auth.models import User
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField
from six import text_type

from course_modes.models import CourseMode
from openedx.core.djangoapps.enrollments.api import validate_course_mode
from openedx.core.djangoapps.enrollments.errors import CourseModeNotFoundError
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_by_name
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.lib.html_to_text import html_to_text
from openedx.core.lib.mail_utils import wrap_message
from student.roles import CourseInstructorRole, CourseStaffRole
from util.keyword_substitution import substitute_keywords_with_data
from util.query import use_read_replica_if_available

log = logging.getLogger(__name__)

# Create your models here.


class user_session_tracking(models.Model):
    """
    Abstract base class for common information for an email.
    """

    user_id = models.IntegerField(max_length=128, blank=False)
    course_name = models.CharField(max_length=128, null=True, blank=True)
    course_id = models.CharField(max_length=128, null=True, blank=True)
    module_name = models.CharField(max_length=128, null=True, blank=True)
    sub_module_name = models.CharField(max_length=128, null=True, blank=True)
    pagein = models.DateTimeField(auto_now_add=True)
    pageout = models.DateTimeField(auto_now=True)
    track_updated = models.IntegerField(max_length=5, null=True, blank=True, default=0)

    def __unicode__(self):
        return self.course_id
