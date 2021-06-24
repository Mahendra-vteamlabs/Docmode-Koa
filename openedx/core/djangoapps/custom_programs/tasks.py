import datetime
import logging
from celery.task import task

from django.conf import settings
from django.shortcuts import redirect
from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from edxmako.shortcuts import render_to_response
from rest_framework.views import APIView
from django.http import JsonResponse
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.djangoapps.custom_programs.models import (
    CustomCourseOverview,
    ProgramAdd,
    ProgramEnrollment,
    ProgramOrder,
    ProgramCoupon,
    CouponRadeemedDetails,
    ProgramCouponRemainUsage,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger("edx.courseware")


@task(bind=True)
def program_course_enrollment(self, course_list, user_id):
    try:
        user = User.objects.get(id=user_id)
        for course in course_list:
            log.info("courses for loop start")
            course_key = CourseKey.from_string(course)
            if not CourseEnrollment.is_enrolled(user, course_key):
                log.info("course enrollment function will be call")
                CourseEnrollment.enroll(
                    user=user, course_key=course_key, mode="no-id-professional"
                )
    except Exception as e:  # pylint: disable=bare-except
        log.exception("Unable to enroll course", exc_info=True)
