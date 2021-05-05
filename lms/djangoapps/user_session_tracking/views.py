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
from lms.djangoapps.reg_form.models import (
    extrafields,
    third_party_user_registration_log,
)
from lms.djangoapps.reg_form.views import getuserfullprofile, userdetails
from lms.djangoapps.specialization.models import (
    specializations,
    categories,
    cat_sub_category,
)
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from student.models import CourseEnrollment
from track.backends.django import TrackingLog
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
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.throttling import UserRateThrottle
from common.djangoapps.organizations.models import (
    Organization,
    OrganizationMembers,
    SponsoringCompany,
    OrganizationSlider,
    Organization_sub_admins,
)

# from common.djangoapps.organizations import serializers
from lms.djangoapps.reg_form.models import extrafields
from lms.djangoapps.specialization.views import specializationName
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.db.models import Count, DateTimeField
from django.core.exceptions import ObjectDoesNotExist

# from lang_pref import LANGUAGE_KEY
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
    SessionAuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from django.http import JsonResponse
from lms.djangoapps.user_session_tracking.models import user_session_tracking

log = logging.getLogger("edx.student")


def create_update_user_session(request):
    user = request.user
    if request.is_ajax():
        if request.method == "GET":
            if user.is_authenticated:
                if "add" in request:
                    usr = request.user.id
                    course_id = request.GET.get("course_id")
                    module_name = request.GET.get("moduleName")
                    sub_module_name = request.GET.get("submoduleName")
                    usession = user_session_tracking(
                        user_id=usr,
                        course_id=course_id,
                        module_name=module_name,
                        sub_module_name=sub_module_name,
                    )
                    usession.save()
                    return HttpResponse(data, status=200, safe=False)

    context = {"course_id": "result"}
    return render_to_response("forum/search_result.html", context)
