import json
import logging
import urllib
import MySQLdb
from collections import OrderedDict
import requests

from django.conf import settings
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, AnonymousUser
from django.template.context_processors import csrf
from django.template.response import TemplateResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q, Count
from django.db.models import Value
from django.db.models.functions import Concat
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import redirect
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from django.views.decorators.http import require_GET, require_POST, require_http_methods

# from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from edxmako.shortcuts import render_to_response, render_to_string, marketing_link
from util.cache import cache, cache_if_anonymous
from lms.djangoapps.reg_form.models import extrafields
from lms.djangoapps.reg_form.views import getuserfullprofile, userdetails
from lms.djangoapps.specialization.models import (
    specializations,
    categories,
    cat_sub_category,
)
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from student.models import CourseEnrollment
from courseware.courses import (
    get_courses,
    get_course,
    get_course_by_id,
    get_permission_for_course_about,
    get_studio_url,
    get_course_overview_with_access,
    get_course_with_access,
    sort_by_announcement,
    sort_by_start_date,
)

from openedx.core.djangoapps.theming import helpers as theming_helpers

from courseware.models import StudentModule

from student.models import User, UserProfile, CourseAccessRole

# from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.throttling import UserRateThrottle
from common.djangoapps.organizations.models import (
    Organization,
    OrganizationMembers,
    SponsoringCompany,
    OrganizationSlider,
)

# from common.djangoapps.organizations import serializers
from lms.djangoapps.reg_form.models import extrafields
from lms.djangoapps.specialization.views import specializationName
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from django.http import JsonResponse
from lms.djangoapps.course_extrainfo.views import (
    category_courses_count,
    category_lectures_count,
    category_casestudies_count,
    course_ctype_number,
)
import datetime
from pytz import UTC, timezone
from datetime import timedelta

# import for course_details api

from lms.djangoapps.course_api.forms import CourseDetailGetForm, CourseListGetForm
from lms.djangoapps.associations.serializers import (
    CourseDetailSerializer,
    CourseSerializer,
)
from lms.djangoapps.course_api.permissions import can_view_courses_for_username

# import for user_profile_api
from lms.djangoapps.userprofile_extrainfo.models import (
    education,
    awards,
    research_papers,
    media_featured,
    clinic_hospital_address,
)
from lms.djangoapps.certificates import api as certificate_api
from openedx.core.djangoapps.user_api.accounts.image_helpers import (
    get_profile_image_urls_for_user,
)

###
from django.dispatch import receiver
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from lms.djangoapps.send_custom_email.models import (
    Custom_email,
    CustomEmailTemplate,
    custom_mail_to_users,
)
from django.core.mail import EmailMultiAlternatives, get_connection
from openedx.core.djangoapps.signals.signals import (
    COURSE_GRADE_NOW_PASSED,
    LEARNER_NOW_VERIFIED,
)
from lms.djangoapps.bulk_email.tasks import _get_course_email_context
from util.date_utils import get_default_time_display, get_time_display

###

log = logging.getLogger("edx.courseware")

template_imports = {"urllib": urllib}

# Create your views here.


def list_categories(request):

    # org_list = []

    category_list = categories.objects.all().order_by("topic_name")
    context = {"categories": category_list}
    return render_to_response("associations/categories.html", context)


@receiver(ENROLL_STATUS_CHANGE)
def send_welcome_email(sender, event=None, user=None, course_id=None, **kwargs):
    log.info("welcome email %s,%s", user, course_id)
    if event == EnrollStatusChange.enroll:
        log.info(u"event->")
        try:
            course_email = Custom_email.objects.get(
                course_id=course_id, template_name="welcome_email.template"
            )

            if course_email:
                try:
                    course_extra_data = course_extrainfo.objects.get(
                        course_id=course_email.course_id
                    )
                except Exception as e:
                    return

                cid1 = str(course_email.course_id)
                userprofile = getuserfullprofile(user.id)
                connection = get_connection()
                connection.open()
                email = user.email
                subject = course_email.subject
                message = (
                    "Congratulations" + user.username + "you are enrolled in the course"
                )

                from_addr = "Docmode - Congratulations <info@docmode.org>"
                course = get_course(course_id)
                course_start_date = get_default_time_display(course.start)
                global_email_context = _get_course_email_context(course)

                email_context = {"name": "", "email": ""}
                email_context.update(global_email_context)
                email_context["email"] = email
                email_context["name"] = userprofile.name
                email_context["user_id"] = user.id
                email_context["course_id"] = course_id
                email_context["start_date"] = course_start_date

                diffdate = course.start - datetime.datetime.now(UTC)
                log.info(u"diffdate %s", diffdate)
                if course_extra_data.google_calendar_url and diffdate.days > 1:
                    log.info(u"diffdate %s", diffdate)
                    email_context[
                        "google_calendar_url"
                    ] = course_extra_data.google_calendar_url
                    email_context["google_calendar_title"] = "Add to calendar"
                    email_context["background_color"] = "4E9CAF"
                else:
                    email_context["google_calendar_url"] = ""
                    email_context["google_calendar_title"] = ""
                    email_context["background_color"] = ""

                email_template = course_email.get_template()
                plaintext_msg = email_template.render_plaintext(
                    course_email.text_message, email_context
                )
                html_msg = email_template.render_htmltext(
                    course_email.html_message, email_context
                )

                email_msg = EmailMultiAlternatives(
                    subject, plaintext_msg, from_addr, [email], connection=connection
                )

                email_msg.attach_alternative(html_msg, "text/html")
                email_msg.send()
                mail_to_users = custom_mail_to_users(
                    course_emailid=course_email.id,
                    user_id=user.id,
                    user_email=email,
                    course_id=course_id,
                )
                mail_to_users.save()
                log.info(u"email_msg2->%s", email_msg)
        except ObjectDoesNotExist:
            log.info("universal welcome email %s,%s", user, course_id)
            try:
                course_email = Custom_email.objects.get(id=3)
            except Exception as e:
                return
            course_extra_data = course_extrainfo.objects.get(course_id=course_id)

            cid1 = str(course_email.course_id)
            userprofile = getuserfullprofile(user.id)
            connection = get_connection()
            connection.open()
            email = user.email

            message = (
                "Congratulations" + user.username + "you are enrolled in the course"
            )

            from_addr = "Docmode - Congratulations <info@docmode.org>"
            course = get_course(course_id)
            course_start_date = get_default_time_display(course.start)
            global_email_context = _get_course_email_context(course)

            email_context = {"name": "", "email": ""}
            email_context.update(global_email_context)
            email_context["email"] = email
            email_context["name"] = userprofile.name
            email_context["user_id"] = user.id
            email_context["course_id"] = course_id
            email_context["start_date"] = course.start.strftime("%b %d, %Y")

            now_asia = course.start.astimezone(timezone("Asia/Kolkata"))
            ctime = now_asia + timedelta(minutes=30)

            email_context["start_time"] = ctime.strftime("%X")

            diffdate = course.start - datetime.datetime.now(UTC)
            total_mins = diffdate.days * 1440 + diffdate.seconds / 60
            log.info(u"total_mins--> %s", total_mins)
            minutes = divmod(diffdate.seconds, 60)
            log.info(u"minutes--> %s", minutes[0])
            if course_extra_data.google_calendar_url and total_mins > 240:

                email_context[
                    "google_calendar_url"
                ] = course_extra_data.google_calendar_url
                email_context["google_calendar_title"] = "Add to calendar"
                email_context["background_color"] = "4E9CAF"
            else:
                email_context["google_calendar_url"] = ""
                email_context["google_calendar_title"] = ""
                email_context["background_color"] = ""

            subject = (
                "Congratulations you are enrolled in " + email_context["course_title"]
            )
            email_template = course_email.get_template()
            plaintext_msg = email_template.render_plaintext(
                course_email.text_message, email_context
            )
            html_msg = email_template.render_htmltext(
                course_email.html_message, email_context
            )

            email_msg = EmailMultiAlternatives(
                subject, plaintext_msg, from_addr, [email], connection=connection
            )

            email_msg.attach_alternative(html_msg, "text/html")
            email_msg.send()
            mail_to_users = custom_mail_to_users(
                course_emailid=course_email.id,
                user_id=user.id,
                user_email=email,
                course_id=course_id,
            )
            mail_to_users.save()


# @receiver(COURSE_GRADE_NOW_PASSED)
def send_course_completion_mail(sender, user, course_id, **kwargs):
    try:
        course_email = Custom_email.objects.get(
            course_id=course_id, template_name="completion_mail.template"
        )
        log.info(u"course_email->%s", course_email)
        if course_email:
            connection = get_connection()
            connection.open()
            log.info("->-> XX == %s ++ %s ++ %s", user, course_id)
            userprofile = getuserfullprofile(user.id)
            email = user.email
            subject = course_email.subject
            message = (
                "Congratulations" + user.username + "you are enrolled in the course"
            )

            from_addr = "dm-stage@docmode.org"
            course = get_course(course_id)
            global_email_context = _get_course_email_context(course)

            email_context = {"name": "", "email": ""}
            email_context.update(global_email_context)
            email_context["email"] = email
            email_context["name"] = userprofile.name
            email_context["user_id"] = user.id
            email_context["course_id"] = course_id

            email_template = course_email.get_template()
            plaintext_msg = email_template.render_plaintext(
                course_email.text_message, email_context
            )
            log.info(u"plaintext_msg %s", plaintext_msg)
            html_msg = email_template.render_htmltext(
                course_email.html_message, email_context
            )
            log.info(u"html_msg %s", html_msg)

            email_msg = EmailMultiAlternatives(
                subject, plaintext_msg, from_addr, [email], connection=connection
            )
            log.info(u"email_msg1->%s", email_msg)
            email_msg.attach_alternative(html_msg, "text/html")
            email_msg.send()
            log.info(u"email_msg2->%s", email_msg)
    except ObjectDoesNotExist:
        course_email = "Not set"
