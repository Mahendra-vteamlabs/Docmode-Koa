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


class Custom_email(models.Model):
    """
    Abstract base class for common information for an email.
    """

    subject = models.CharField(max_length=128, blank=True)
    html_message = models.TextField(null=True, blank=True)
    text_message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    template_name = models.CharField(null=True, max_length=255)

    def __unicode__(self):
        return self.subject

    @classmethod
    def create(
        cls,
        course_id,
        sender,
        targets,
        subject,
        html_message,
        text_message=None,
        template_name=None,
        from_addr=None,
    ):
        """
        Create an instance of CourseEmail.
        """
        # automatically generate the stripped version of the text from the HTML markup:
        if text_message is None:
            text_message = html_to_text(html_message)

        # create the task, then save it immediately:
        course_email = cls(
            course_id=course_id,
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            template_name=template_name,
        )
        course_email.save()  # Must exist in db before setting M2M relationship values
        course_email.targets.add(*new_targets)
        course_email.save()

        return course_email

    def get_template(self):
        """
        Returns the corresponding CustomEmailTemplate for this CourseEmail.
        """
        return CustomEmailTemplate.get_template(name=self.template_name)


COURSE_EMAIL_MESSAGE_BODY_TAG = "{{message_body}}"


class CustomEmailTemplate(models.Model):
    """
    Stores templates for all emails to a course to use.

    This is expected to be a singleton, to be shared across all courses.
    Initialization takes place in a migration that in turn loads a fixture.
    The admin console interface disables add and delete operations.
    Validation is handled in the CustomEmailTemplateForm class.
    """

    html_template = models.TextField(null=True, blank=True)
    plain_template = models.TextField(null=True, blank=True)
    name = models.CharField(null=True, max_length=255, unique=True, blank=True)

    @staticmethod
    def get_template(name=None):
        """
        Fetch the current template

        If one isn't stored, an exception is thrown.
        """
        try:
            return CustomEmailTemplate.objects.get(name=name)
        except CustomEmailTemplate.DoesNotExist:
            log.exception("Attempting to fetch a non-existent course email template")
            raise

    @staticmethod
    def _render(format_string, message_body, context):
        """
        Create a text message using a template, message body and context.

        Convert message body (`message_body`) into an email message
        using the provided template.  The template is a format string,
        which is rendered using format() with the provided `context` dict.

        Any keywords encoded in the form %%KEYWORD%% found in the message
        body are substituted with user data before the body is inserted into
        the template.

        Output is returned as a unicode string.  It is not encoded as utf-8.
        Such encoding is left to the email code, which will use the value
        of settings.DEFAULT_CHARSET to encode the message.
        """

        # Substitute all %%-encoded keywords in the message body
        if "user_id" in context and "course_id" in context:
            message_body = substitute_keywords_with_data(message_body, context)

        result = format_string.format(**context)

        # Note that the body tag in the template will now have been
        # "formatted", so we need to do the same to the tag being
        # searched for.
        message_body_tag = COURSE_EMAIL_MESSAGE_BODY_TAG.format()
        result = result.replace(message_body_tag, message_body, 1)

        # finally, return the result, after wrapping long lines and without converting to an encoded byte array.
        return wrap_message(result)

    def render_plaintext(self, plaintext, context):
        """
        Create plain text message.

        Convert plain text body (`plaintext`) into plaintext email message using the
        stored plain template and the provided `context` dict.
        """
        return CustomEmailTemplate._render(self.plain_template, plaintext, context)

    def render_htmltext(self, htmltext, context):
        """
        Create HTML text message.

        Convert HTML text body (`htmltext`) into HTML email message using the
        stored HTML template and the provided `context` dict.
        """
        # HTML-escape string values in the context (used for keyword substitution).
        for key, value in context.iteritems():
            if isinstance(value, basestring):
                context[key] = markupsafe.escape(value)
        return CustomEmailTemplate._render(self.html_template, htmltext, context)


class custom_mail_to_users(models.Model):
    course_emailid = models.CharField(max_length=128, blank=True)
    user_id = models.CharField(max_length=128, blank=True)
    user_email = models.CharField(max_length=128, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    course_id = models.CharField(max_length=128, blank=True, default="N/a")

    def __unicode__(self):
        return self.user_email
