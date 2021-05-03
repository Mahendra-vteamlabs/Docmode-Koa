"""
Associations views functions
"""

import json
import ast
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

# from track.backends.django import TrackingLog
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
    Organization_sub_admins,
)

# from organizations import serializers
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
from pytz import UTC

# import for course_details api

from lms.djangoapps.course_api.forms import CourseDetailGetForm, CourseListGetForm
from lms.djangoapps.associations.serializers import (
    CourseDetailSerializer,
    CourseSerializer,
    Custom_CourseDetailSerializer,
    Custom_CourseSerializer,
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

# for custom email
from django.dispatch import receiver
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from lms.djangoapps.bulk_email.models import BulkEmailFlag, CourseEmail
from lms.djangoapps.bulk_email.tasks import _get_course_email_context
from django.core.mail import EmailMultiAlternatives, get_connection
from openedx.core.djangoapps.signals.signals import (
    COURSE_GRADE_NOW_PASSED,
    LEARNER_NOW_VERIFIED,
)
from lms.djangoapps.grades.models import PersistentCourseGrade

###

###
from django.dispatch import receiver
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from lms.djangoapps.send_custom_email.models import Custom_email, CustomEmailTemplate
from django.core.mail import EmailMultiAlternatives, get_connection
from openedx.core.djangoapps.signals.signals import (
    COURSE_GRADE_NOW_PASSED,
    LEARNER_NOW_VERIFIED,
)

###

# for third party user registration
from openedx.core.djangoapps.user_authn.views.registration_form import (
    AccountCreationForm,
)
from student.helpers import (
    AccountValidationError,
    create_or_set_user_attribute_created_on_site,
    generate_activation_email_context,
    get_next_url_for_login_page,
)
from student.models import (
    CourseAccessRole,
    CourseEnrollment,
    LoginFailures,
    Registration,
    UserProfile,
    anonymous_id_for_user,
    create_comments_service_user,
)
from student.helpers import authenticate_new_user, do_create_account
from openedx.core.djangoapps.user_authn.utils import generate_password
from django.core.validators import ValidationError, validate_email

# import ends here

### for user session tracking on course page###
from lms.djangoapps.user_session_tracking.models import user_session_tracking
from pytz import UTC, timezone
from django.contrib.auth import login as django_login

log = logging.getLogger("edx.courseware")

template_imports = {"urllib": urllib}

# Create your views here.


def index(request):
    if not request.user.is_staff:
        main_url = "https://docmode.org/"
        new_url = main_url + "our-partner/"
        return redirect(new_url)
    from organizations.api import get_organizations

    # org_list = []

    org_list = get_organizations()

    sorted_assoc_list = sorted(
        org_list, key=lambda organizations: organizations["name"]
    )

    context = {"organizations": sorted_assoc_list}

    return render_to_response("associations/associations.html", context)


# def list_categories(request):

#     # org_list = []

#     category_list = categories.objects.all().order_by('topic_name')
#     context = {
#       'categories' : category_list
#     }
#     return render_to_response("associations/categories.html",context)


def list_lectures(request):
    if not request.user.is_staff:
        main_url = "https://docmode.org/lectures"
        return redirect(main_url)
    # HEMANT
    # enable_mktg_site = configuration_helpers.get_value(
    #    'ENABLE_MKTG_SITE',
    #    settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    # )

    # if enable_mktg_site:
    #    return redirect(marketing_link('LECTURES'), permanent=True)

    # if not settings.FEATURES.get('COURSES_ARE_BROWSABLE'):
    #    raise Http404
    # HEMANT
    from lms.djangoapps.course_extrainfo.models import course_extrainfo

    # lectures_list = []

    lectures = course_extrainfo.objects.filter(course_type=2).values()
    cid = []
    for courseid in lectures:
        course_id = CourseKey.from_string(courseid["course_id"])
        cid.append(course_id)
    course_data = (
        CourseOverview.objects.all()
        .filter(pk__in=cid, catalog_visibility="both")
        .order_by("-start")[:130]
    )
    course_discovery_meanings = getattr(settings, "COURSE_DISCOVERY_MEANINGS", {})

    context = {
        "lectures_list": course_data,
        "course_discovery_meanings": course_discovery_meanings,
    }
    return render_to_response("associations/lectures.html", context)


def case_study(request):
    from lms.djangoapps.course_extrainfo.models import course_extrainfo

    # case_studies_list = []

    course_cat = course_extrainfo.objects.filter(course_type=3).values()
    cid = []
    for courseid in course_cat:
        course_id = CourseKey.from_string(courseid["course_id"])
        cid.append(course_id)

    course_data = (
        CourseOverview.objects.all().filter(pk__in=cid).order_by("start")[::-1]
    )
    course_discovery_meanings = getattr(settings, "COURSE_DISCOVERY_MEANINGS", {})

    context = {
        "courses": course_data,
        "course_discovery_meanings": course_discovery_meanings,
    }
    return render_to_response("associations/case_studies.html", context)


@login_required
def case_study_form(request):

    context = {"user": request.user}
    return render_to_response("associations/case_study_form.html", context)


def stateName(stateId):
    from django.core.exceptions import ObjectDoesNotExist

    statename = ""
    try:
        getDetails = states.objects.get(id=stateId)
        statename = getDetails.rstate
    except ObjectDoesNotExist:
        getDetails = None

    return HttpResponse(statename)


@ensure_csrf_cookie
@cache_if_anonymous()
def association_about(request, organization_id):
    if not request.user.is_staff:
        main_url = "https://docmode.org/"
        new_url = main_url + organization_id
        return redirect(new_url)
    """
    Display the association's about page.
    """
    user = request.user
    from organizations.models import (
        Organization,
        OrganizationCourse,
        OrganizationSlider,
        OrganizationMembers,
    )

    # from courseware.courses import get_course
    from django.core.exceptions import ObjectDoesNotExist

    try:
        data = Organization.objects.get(short_name=organization_id)
        if data:

            speczs = extrafields.objects.values("specialization").annotate(
                dcount=Count("specialization")
            )

            try:
                courses = (
                    CourseOverview.objects.all()
                    .filter(
                        display_org_with_default=organization_id,
                        catalog_visibility="both",
                    )
                    .order_by("start")[::-1]
                )
            except ObjectDoesNotExist:
                courses = None

            try:
                uc_courses = (
                    CourseOverview.objects.all()
                    .filter(
                        Q(display_org_with_default=organization_id)
                        & Q(start__gte=datetime.date.today())
                        & Q(catalog_visibility="both")
                    )
                    .order_by("start")
                )
            except ObjectDoesNotExist:
                uc_courses = None

            usertypes = extrafields.objects.values("user_type").annotate(
                dcount=Count("user_type")
            )

            orgmembers = OrganizationMembers.objects.values("organization_id").annotate(
                dcount=Count("organization_id")
            )

            if request.is_ajax():
                if request.method == "GET":
                    if user.is_authenticated():
                        usr = request.user.id
                        usrmail = request.user.email
                        gid = request.GET.get("groupid")
                        group = Organization.objects.get(id=gid)

                        gmember = OrganizationMembers(
                            user_id=usr, organization=group, user_email=usrmail
                        )
                        gmember.save()
                        return HttpResponse("Joined succesful")

            try:
                slider_images = OrganizationSlider.objects.get(organization_id=data.id)
                sep_images = slider_images.image_s3_urls
            except ObjectDoesNotExist:
                slider_images = None
                sep_images = "http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg"

            # if slider_images is None:
            #   sep_images = 'http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg'
            # else:
            #   sep_images = slider_images.image_s3_urls

            imgs = sep_images.split(",")
            no_of_slides = len(imgs)
            gusr = request.user.id
            gusr_staff = request.user.is_staff
            try:
                member = OrganizationMembers.objects.get(
                    user_id=gusr, organization_id=data.id
                )
            except ObjectDoesNotExist:
                member = None

            try:
                member_staff = OrganizationMembers.objects.get(
                    user_id=gusr, organization_id=data.id, is_admin="1"
                )
                # member_staff = OrganizationMembers.objects.get(user_id=gusr,organization_id=data.id)
            except ObjectDoesNotExist:
                member_staff = None

            if member is None:
                grpmember = "0"
            else:
                grpmember = "1"

            if member_staff is None:
                grpstaff = "0"
            else:
                grpstaff = "1"

            context = {
                "association_id": data.id,
                "assoc_name": data.name,
                "assoc_short_name": data.short_name,
                "assoc_description": data.description,
                "assoc_logo": data.logo,
                "org_promo_video": data.org_promo_video,
                "courses": courses,
                "uc_lect": uc_courses,
                "speczs": speczs,
                "orgmembers": orgmembers,
                "usertypes": usertypes,
                "slider_images": imgs,
                "no_of_slides": no_of_slides,
                "csrf": csrf(request)["csrf_token"],
                "grpmember": grpmember,
                "gusr_staff": grpstaff,
            }
        return render_to_response("associations/association_about.html", context)

    except ObjectDoesNotExist:
        notfound = None
        return HttpResponseRedirect(reverse("root"))


def category(request, category_id):
    """
    Display the subjects page
    """
    # from courseware.courses import get_course
    from django.core.exceptions import ObjectDoesNotExist
    from lms.djangoapps.course_extrainfo.models import course_extrainfo

    try:
        cat = categories.objects.get(topic_short_name=category_id)
    except ObjectDoesNotExist:
        cat = None

    try:
        subcat = cat_sub_category.objects.filter(category_id=cat.id)
    except ObjectDoesNotExist:
        subcat = None

    try:
        course_cat = course_extrainfo.objects.filter(category=cat.id).values()
    except ObjectDoesNotExist:
        course_cat = None

    cid = []
    for courseid in course_cat:
        course_id = CourseKey.from_string(courseid["course_id"])
        cid.append(course_id)

    course_data = (
        CourseOverview.objects.all()
        .filter(pk__in=cid, catalog_visibility="both")
        .order_by("start")[::-1]
    )

    try:
        course_cat_count = course_extrainfo.objects.filter(category=cat.id).count()
    except ObjectDoesNotExist:
        course_cat_count = "No result found"

    if request.is_ajax():
        if request.method == "POST":
            subcatid = request.POST.get("subcategoryid")
            course_time = request.POST.get("coursetime")
            if subcatid > "0":
                try:
                    subcat_courses = course_extrainfo.objects.filter(
                        category=cat.id, sub_category__contains=subcatid
                    ).values()
                except ObjectDoesNotExist:
                    subcat_courses = None

                scid = []
                for courseid in subcat_courses:
                    sub_course_id = CourseKey.from_string(courseid["course_id"])
                    scid.append(sub_course_id)

                if course_time == "1":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(
                            Q(pk__in=scid)
                            & Q(start__lte=datetime.date.today())
                            & Q(catalog_visibility="both")
                        )
                        .order_by("start")[::-1]
                    )
                elif course_time == "2":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(
                            Q(pk__in=scid)
                            & Q(start__gte=datetime.date.today())
                            & Q(catalog_visibility="both")
                        )
                        .order_by("start")[::-1]
                    )
                else:
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(pk__in=scid, catalog_visibility="both")
                        .order_by("start")[::-1]
                    )

            else:
                if course_time == "1":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(
                            Q(pk__in=cid)
                            & Q(start__lte=datetime.date.today())
                            & Q(catalog_visibility="both")
                        )
                        .order_by("start")[::-1]
                    )
                elif course_time == "2":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(
                            Q(pk__in=cid)
                            & Q(start__gte=datetime.date.today())
                            & Q(catalog_visibility="both")
                        )
                        .order_by("start")[::-1]
                    )
                else:
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(pk__in=cid, catalog_visibility="both")
                        .order_by("start")[::-1]
                    )

            html = render_to_string(
                "associations/courses.html", {"courses": sub_course_data}
            )
            return HttpResponse(html)

    context = {
        "category": cat,
        "count": course_cat_count,
        "courses": course_data,
        "subcat": subcat,
    }

    return render_to_response("associations/category_courses.html", context)


def course_det(courseId):

    course_key = CourseKey.from_string(courseId)

    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

    course_details = CourseOverview.objects.all().filter(id=course_key).values()

    return course_details


def speczName(speczId):
    from django.core.exceptions import ObjectDoesNotExist

    speczname = ""
    try:
        getDetails = specializations.objects.get(id=speczId)
        speczname = getDetails.name
    except ObjectDoesNotExist:
        getDetails = None

    return speczname


def orgName(orgId):
    from django.core.exceptions import ObjectDoesNotExist
    from organizations.models import (
        Organization,
        OrganizationCourse,
        OrganizationSlider,
        OrganizationMembers,
    )

    orgname = ""
    try:
        getDetails = Organization.objects.get(id=orgId)
        orgname = getDetails.name
    except ObjectDoesNotExist:
        getDetails = None

    return orgname


def userType(type):
    from django.core.exceptions import ObjectDoesNotExist

    ust = ""
    if type == "dr":
        ust = "Doctor"
    elif type == "u":
        ust = "User"
    elif type == "ms":
        ust = "Medical Student"
    elif type == "hc":
        ust = "Healthcare Specialist"

    return ust


@ensure_csrf_cookie
@cache_if_anonymous()
def organization_analytics(request, organization_id):
    """
    Display the association's about page.
    """
    user = request.user
    from organizations.models import (
        Organization,
        OrganizationCourse,
        OrganizationSlider,
        OrganizationMembers,
    )

    # from courseware.courses import get_course
    from django.core.exceptions import ObjectDoesNotExist

    data = Organization.objects.get(id=organization_id)

    speczs = extrafields.objects.values("specialization").annotate(
        dcount=Count("specialization")
    )

    usertypes = extrafields.objects.values("user_type").annotate(
        dcount=Count("user_type")
    )

    orgmembers = OrganizationMembers.objects.values("organization").annotate(
        dcount=Count("organization")
    )

    courses = OrganizationCourse.objects.all().filter(organization_id=organization_id)
    if request.is_ajax():
        if request.method == "GET":
            if user.is_authenticated():
                cities = extrafields.objects.values("regstate").annotate(
                    dcount=Count("regstate")
                )
                city_dict = {}
                for city in cities:
                    city_dict[city["regstate"]] = city["dcount"]

                return HttpResponse(
                    json.dumps(city_dict), content_type="application/json"
                )

    try:
        slider_images = OrganizationSlider.objects.filter(
            organization_id=organization_id
        )
    except ObjectDoesNotExist:
        slider_images = None

    if slider_images is None:
        sep_images = "http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg"
    else:
        sep_images = "http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg"

    imgs = sep_images.split(",")
    no_of_slides = len(imgs)
    gusr = request.user.id
    try:
        member = OrganizationMembers.objects.get(
            user_id=gusr, organization=organization_id
        )
    except ObjectDoesNotExist:
        member = None

    if member is None:
        grpmember = "0"
    else:
        grpmember = "1"

    context = {
        "association_id": data.id,
        "assoc_name": data.name,
        "assoc_short_name": data.short_name,
        "assoc_description": data.description,
        "courses": courses,
        "slider_images": imgs,
        "no_of_slides": no_of_slides,
        "csrf": csrf(request)["csrf_token"],
        "grpmember": grpmember,
    }

    return render_to_response("associations/analytics.html", context)


def get_user_type(sname):
    if sname == "dr":
        uName = "Doctor"
    elif sname == "hc":
        uName = "Healthcare"
    elif sname == "ms":
        uName = "Medical Student"
    else:
        uName = "Public"
    return uName


def getuserlog(cid):
    usercnt = ""
    try:
        usercnt = TrackingLog.objects.filter(event_type__contains=cid).count()
    except ObjectDoesNotExist:
        usercnt = None

    return usercnt


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def custom_analytics(request):
    """Render the custom analytics page for docmode.

    Args:
       request (HttpRequest)

    Returns:
       HttpResponse: 200 if the page was sent successfully
       HttpResponse: 302 if not logged in (redirect to login page)
       HttpResponse: 405 if using an unsupported HTTP method
    Raises:
       Http404: 404 if the specified user is not authorized or does not exist

    Example usage:
       GET /account/profile
    """
    user = request.user
    import datetime

    # if (user.email == 'hemant@docmode.com') or (user.email == 'paulson@docmode.com') or (user.email == 'dev@docmode.com'):
    if user.is_staff:
        from opaque_keys.edx.locations import SlashSeparatedCourseKey

        total_users = User.objects.count()
        users_not_verified = User.objects.filter(is_active=0).count()
        verified_users = User.objects.filter(is_active=1).count()
        total_assoc = Organization.objects.count()
        webinar_count = course_extrainfo.objects.filter(course_type="2").count()
        course_count = course_extrainfo.objects.filter(course_type="1").count()
        usertypes = (
            extrafields.objects.exclude(user_type="")
            .values("user_type")
            .annotate(dcount=Count("user_type"))
            .order_by()
        )
        specQset = (
            extrafields.objects.filter(user_type="dr")
            .exclude(specialization_id__isnull=True)
            .values("specialization_id")
            .annotate(dcount=Count("specialization_id"))
            .order_by()
        )
        hcQset = (
            extrafields.objects.filter(user_type="hc")
            .exclude(hcspecialization_id__isnull=True)
            .values("hcspecialization_id")
            .annotate(dcount=Count("hcspecialization_id"))
            .order_by()
        )
        orgMemQset = (
            OrganizationMembers.objects.values("organization_id")
            .annotate(dcount=Count("user_id"))
            .order_by()
        )
        month_wise_reg = (
            User.objects.values("date_joined")
            .annotate(dcount=Count("date_joined"))
            .order_by()
        )
        course_all = CourseOverview.objects.values("id")
        # course_user_dict = {}
        # for courseid in course_all:
        #     cid = courseid['id'] + '/courseware/'
        #     course_user_dict[cid] = getuserlog(cid)

        # course_viewd_user_cnt = TrackingLog.objects.filter(event_type__contains=course_all).count()
        def specData():
            # sn = []
            # sn.append(['Specialization', 'User Count'])
            # for n in specQset:
            #   sn.append([specializationName(n['specialization_id']),n['dcount']])
            sn = [
                [
                    specializationName(sn["specialization_id"]).encode("ASCII"),
                    sn["dcount"],
                ]
                for sn in specQset
            ]
            return sn

        def userTypes():
            ut = []
            for k in usertypes:
                ut.append(get_user_type(k["user_type"]))
            return ut

        def userCount():
            ut = []
            for k in usertypes:
                ut.append(k["dcount"])
            return ut

        context = {
            "total_users": total_users,
            "users_not_verified": users_not_verified,
            "verified_users": verified_users,
            "total_assoc": total_assoc,
            "webinar_count": webinar_count,
            "course_count": course_count,
            "usertype_qset": usertypes,
            "spec_data": specData(),
            "spec_qset": specQset,
            "orgMemQset": orgMemQset,
            "hc_qset": hcQset,
            "mwr": month_wise_reg,
            "cal": course_all,
        }

        return render_to_response("custom_analytics/custom_analytics.html", context)
    else:
        return HttpResponse("Not Authorized!")


@login_required
@ensure_csrf_cookie
def export_specz_usercount_csv(request):
    import csv
    from django.utils.encoding import smart_str

    specQset = (
        extrafields.objects.filter(user_type="dr")
        .exclude(specialization_id__isnull=True)
        .values("specialization_id")
        .annotate(dcount=Count("specialization_id"))
        .order_by("-dcount")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        "attachment; filename=Specialization_usercount_"
        + str(datetime.date.today())
        + ".csv"
    )
    writer = csv.writer(response, csv.excel)
    # BOM (optional...Excel needs it to open UTF-8 file properly)
    response.write(u"\ufeff".encode("utf8"))
    # log.info(u" coupondata %s", coupon_results)
    user = request.user

    if user.is_staff:
        writer.writerow(
            [
                smart_str(u"Specialization"),
                smart_str(u"Count"),
            ]
        )
        response["Content-Disposition"] = (
            "attachment; filename=Specialization_usercount_"
            + str(datetime.date.today())
            + ".csv"
        )
        for sn in specQset:
            writer.writerow(
                [
                    smart_str(specializationName(sn["specialization_id"])),
                    smart_str(sn["dcount"]),
                ]
            )

    return response


export_specz_usercount_csv.short_description = u"Export Specialization Usercount CSV"


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def custom_analytics_coupons(request):
    # from opaque_keys.edx.locations import SlashSeparatedCourseKey
    # cid = 'mindvision/LMV004/2017_May_LMV004'
    # cid = SlashSeparatedCourseKey.from_deprecated_string(cid)
    # enrollLocationQset = CourseEnrollment.objects.filter(course_id=cid).count()
    # extrafields.objects.filter(user_type='dr').exclude(specialization_id__isnull=True).values('specialization_id').annotate(dcount=Count('specialization_id')).order_by()

    db = MySQLdb.connect(
        "hawthorn-live.c2woekolusus.ap-south-1.rds.amazonaws.com",
        "ecomm001",
        "HjDzeQZlRJcXoRadc8fRnS8HDnlky450mhL",
        "ecommerce",
    )

    # define a cursor object
    cursor = db.cursor()
    sql = "select *,COUNT(*) as count,SUM(num_orders) as total_orders from voucher_voucher group by name order by start_datetime desc"
    cursor.execute(sql)
    results = cursor.fetchall()
    db.close()

    context = {
        # 'title': 'Demographics Page',
        # 'locationCount': enrollLocationQset
        "vouchers": results
    }

    return render_to_response("custom_analytics/custom_analytics_coupons.html", context)


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def coupon_details(request, coupon_name):

    db = MySQLdb.connect(
        "hawthorn-live.c2woekolusus.ap-south-1.rds.amazonaws.com",
        "ecomm001",
        "HjDzeQZlRJcXoRadc8fRnS8HDnlky450mhL",
        "ecommerce",
    )
    coupon_name = coupon_name
    # define a cursor object
    cursor = db.cursor()
    cursor.execute(
        "SELECT voucher_voucher.id, voucher_voucher.name,voucher_voucher.code,voucher_voucherapplication.date_created,voucher_voucherapplication.order_id,voucher_voucherapplication.user_id,voucher_voucherapplication.voucher_id,ecommerce_user.id,ecommerce_user.email,ecommerce_user.first_name,ecommerce_user.last_name FROM voucher_voucher INNER JOIN voucher_voucherapplication on voucher_voucher.id = voucher_voucherapplication.voucher_id INNER JOIN ecommerce_user on voucher_voucherapplication.user_id = ecommerce_user.id WHERE name = %s",
        [coupon_name],
    )
    results = cursor.fetchall()
    # voucherid = results[0][0]
    # log.info(u" Order_Voucherid %s", voucherid)
    # order = db.cursor()
    # order.execute("SELECT * from voucher_voucherapplication WHERE voucher_id = %s",[results[0][0]])
    # corder = order.fetchall()
    db.close()

    context = {"coupon": results}

    return render_to_response(
        "custom_analytics/custom_analytics_coupon_details.html", context
    )


def export_coupon_csv(request, coupon_name):
    import csv
    from django.utils.encoding import smart_str

    db = MySQLdb.connect(
        "hawthorn-live.c2woekolusus.ap-south-1.rds.amazonaws.com",
        "ecomm001",
        "HjDzeQZlRJcXoRadc8fRnS8HDnlky450mhL",
        "ecommerce",
    )
    coupon_name = coupon_name
    # define a cursor object
    coupon_cursor = db.cursor()
    coupon_cursor.execute(
        "SELECT voucher_voucher.id, voucher_voucher.name,voucher_voucher.code,voucher_voucherapplication.date_created,voucher_voucherapplication.order_id,voucher_voucherapplication.user_id,voucher_voucherapplication.voucher_id,ecommerce_user.id,ecommerce_user.email,ecommerce_user.first_name,ecommerce_user.last_name FROM voucher_voucher INNER JOIN voucher_voucherapplication on voucher_voucher.id = voucher_voucherapplication.voucher_id INNER JOIN ecommerce_user on voucher_voucherapplication.user_id = ecommerce_user.id WHERE voucher_voucher.name = %s",
        [coupon_name],
    )
    coupon_results = coupon_cursor.fetchall()
    db.close()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        "attachment; filename="
        + coupon_name
        + "_"
        + str(datetime.date.today())
        + ".csv"
    )
    writer = csv.writer(response, csv.excel)
    # BOM (optional...Excel needs it to open UTF-8 file properly)
    response.write(u"\ufeff".encode("utf8"))
    # log.info(u" coupondata %s", coupon_results)
    user = request.user

    if user.is_staff:
        writer.writerow(
            [
                smart_str(u"Coupon Code"),
                smart_str(u"Emailid"),
                smart_str(u"Name"),
                smart_str(u"Phone"),
                smart_str(u"State"),
                smart_str(u"City"),
                smart_str(u"Date"),
            ]
        )
        response["Content-Disposition"] = (
            "attachment; filename="
            + coupon_name
            + "_"
            + str(datetime.date.today())
            + ".csv"
        )
        for coupon in coupon_results:
            cuser = User.objects.filter(email=coupon[8]).values("id")
            user_phone = userdetails(cuser)
            user_profile = getuserfullprofile(cuser)
            writer.writerow(
                [
                    smart_str(coupon[2].encode("ASCII")),
                    smart_str(coupon[8]),
                    smart_str(user_profile.name),
                    smart_str(user_phone.phone),
                    smart_str(user_phone.rstate),
                    smart_str(user_phone.rcity),
                    smart_str(coupon[3]),
                ]
            )

    return response


export_coupon_csv.short_description = u"Export Coupon CSV"


@login_required
@ensure_csrf_cookie
def order_details(request):

    db = MySQLdb.connect(
        "hawthorn-live.c2woekolusus.ap-south-1.rds.amazonaws.com",
        "ecomm001",
        "HjDzeQZlRJcXoRadc8fRnS8HDnlky450mhL",
        "ecommerce",
    )
    cursor = db.cursor()
    cursor.execute(
        "SELECT order_order.id,order_order.number,order_order.status,order_order.user_id,order_order.total_incl_tax,order_order.date_placed,ecommerce_user.id,ecommerce_user.email,order_orderdiscount.amount,order_orderdiscount.order_id from order_order INNER JOIN ecommerce_user on ecommerce_user.id=order_order.user_id INNER JOIN order_orderdiscount on order_orderdiscount.order_id = order_order.id where order_order.status='complete' and ecommerce_user.email not like'%docmode%'"
    )
    results = cursor.fetchall()
    db.close()
    List = list()
    for result in results:
        # log.info(u'od_result-> %s', result)
        result = list(result)
        try:
            user_details = User.objects.get(email=result[7])
            user_extrainfo = extrafields.objects.get(user_id=user_details.id)
            result.append(user_extrainfo.rstate)
            List.append(result)
        except ObjectDoesNotExist:
            user_extrainfo = "N/A"
        # user_dict['order_id']=result[0]
        # user_dict['email'] = result[6]
        # user_dict['amount'] = result[3],
        # user_dict['date'] = result[4],
        # user_dict['state'] = user_extrainfo.rstate
        # user_order_details.append(user_dict)
    torder_results = tuple(List)
    context = {"orders": torder_results}

    return render_to_response("custom_analytics/custom_analytics_orders.html", context)


def export_order_csv(request):
    import csv
    from django.utils.encoding import smart_str

    db = MySQLdb.connect(
        "hawthorn-live.c2woekolusus.ap-south-1.rds.amazonaws.com",
        "ecomm001",
        "HjDzeQZlRJcXoRadc8fRnS8HDnlky450mhL",
        "ecommerce",
    )
    cursor = db.cursor()
    cursor.execute(
        "SELECT order_order.number,order_order.status,order_order.user_id,order_order.total_incl_tax,order_order.date_placed,ecommerce_user.id,ecommerce_user.email from order_order INNER JOIN ecommerce_user on ecommerce_user.id=order_order.user_id where order_order.status='complete' and ecommerce_user.email not like'%docmode%'"
    )
    results = cursor.fetchall()
    db.close()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        "attachment; filename=Docmode_orders_" + str(datetime.date.today()) + ".csv"
    )
    writer = csv.writer(response, csv.excel)
    # BOM (optional...Excel needs it to open UTF-8 file properly)
    response.write(u"\ufeff".encode("utf8"))
    # log.info(u" coupondata %s", coupon_results)
    user = request.user

    if user.is_staff:
        writer.writerow(
            [
                smart_str(u"Order number"),
                smart_str(u"Emailid"),
                smart_str(u"Amount"),
                smart_str(u"State"),
                smart_str(u"Date"),
            ]
        )
        response["Content-Disposition"] = (
            "attachment; filename=Docmode_orders_" + str(datetime.date.today()) + ".csv"
        )
        for result in results:
            cuser = User.objects.filter(email=result[6]).values("id")
            user_phone = userdetails(cuser)
            user_profile = getuserfullprofile(cuser)
            writer.writerow(
                [
                    smart_str(result[0]),
                    smart_str(result[6]),
                    smart_str(result[3]),
                    smart_str(user_phone.rstate),
                    smart_str(result[4].strftime("%Y-%m-%d")),
                ]
            )

    return response


export_coupon_csv.short_description = u"Export Order CSV"


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def custom_analytics_viewership(request):
    def getState(userId):
        statename = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            statename = getDetails.rstate
        except ObjectDoesNotExist:
            getDetails = None

        return statename

    def getCity(userId):
        cityname = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            cityname = getDetails.rcity
        except ObjectDoesNotExist:
            getDetails = None

        return cityname

    def getViewerName(userId):
        vName = ""
        try:
            getDetails = UserProfile.objects.get(user_id=userId)
            vName = getDetails.name
        except ObjectDoesNotExist:
            getDetails = None

        return vName

    def getViewerEmail(userId):
        vEmail = ""
        try:
            getDetails = User.objects.get(id=userId)
            vEmail = getDetails.email
        except ObjectDoesNotExist:
            getDetails = None

        return vEmail

    if request.is_ajax():
        if "courseid" in request.GET:
            from opaque_keys.edx.locations import SlashSeparatedCourseKey

            cid = request.GET.get("courseid")
            cid = SlashSeparatedCourseKey.from_deprecated_string(cid)
            count = StudentModule.objects.filter(
                course_id=cid, module_type="video"
            ).count()
            crows = StudentModule.objects.filter(
                Q(module_type="video") & Q(course_id=cid)
            ).values("state", "student_id", "course_id")
            rows = [
                [
                    s["state"].encode("ASCII"),
                    getViewerName(s["student_id"]).encode("ASCII"),
                    getViewerEmail(s["student_id"]),
                    getState(s["student_id"]),
                    getCity(s["student_id"]),
                    s["course_id"],
                ]
                for s in crows
            ]

            user_dict = {}
            for row in crows:
                user_dict["name"] = getViewerName(row["student_id"]).encode("ASCII")
                user_dict["state"] = getState(row["student_id"]).encode("ASCII")
                user_dict["city"] = getCity(row["student_id"]).encode("ASCII")
                user_dict["email"] = getViewerEmail(row["student_id"]).encode("ASCII")
                user_dict["viewed"] = row["state"].encode("ASCII")

            return HttpResponse(json.dumps(user_dict), content_type="application/json")
        else:
            data = request.GET
            courseid = data.get("term")
            if courseid:
                courses = CourseOverview.objects.filter(id__icontains=courseid)
            else:
                courses = CourseOverview.objects.all()
            results = []
            for course in courses:
                course_json = {}
                course_json["id"] = course.display_number_with_default
                course_json["label"] = course.display_name
                course_json["value"] = course.display_name
                results.append(course_json)

            data = json.dumps(results)
            mimetype = "application/json"
            return HttpResponse(data, mimetype)

    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    course_id = SlashSeparatedCourseKey.from_deprecated_string(
        "docmode/dm002/2017_dm002"
    )

    viewersQset = StudentModule.objects.filter(Q(module_type="video")).values(
        "state", "student_id", "course_id"
    )
    rows = [
        [
            s["state"].encode("ASCII"),
            getViewerName(s["student_id"]).encode("ASCII"),
            getViewerEmail(s["student_id"]),
            getState(s["student_id"]),
            getCity(s["student_id"]),
            s["course_id"],
        ]
        for s in viewersQset
    ]
    courses = CourseOverview.objects.all()
    context = {
        "title": "Viewership Page",
        "qset": viewersQset,
        "rows": rows,
        "courses": courses,
    }

    return render_to_response(
        "custom_analytics/custom_analytics_viewership.html", context
    )


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def association_dashboard(request, org_sname):

    from organizations.models import OrganizationCourse, OrganizationMembers

    gusr = request.user.id
    data = Organization.objects.get(short_name=org_sname)
    try:
        member_staff = OrganizationMembers.objects.get(
            user_id=gusr, organization_id=data.id, is_admin="1"
        )
        if member_staff.course_ids != "":
            admin_courseids = member_staff.course_ids.split(",")
            cid = []
            for courseid in admin_courseids:
                course_id = CourseKey.from_string(courseid)
                cid.append(course_id)
        else:
            cid = "None"
    except ObjectDoesNotExist:
        member_staff = None
        cid = None

    if member_staff is None:
        grpstaff = "0"
    else:
        grpstaff = "1"

    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    course_id = SlashSeparatedCourseKey.from_deprecated_string(
        "course-v1:DRL+DRL002+2020_Dec_DRL002"
    )

    getDetails = (
        StudentModule.objects.filter(course_id=course_id)
        .values("student_id")
        .distinct()
    )
    log.info("viewer--> %s", len(getDetails))
    try:
        courses = (
            CourseOverview.objects.all()
            .filter(
                Q(display_org_with_default=org_sname) & Q(catalog_visibility="both")
            )
            .order_by("-start")
        )
    except ObjectDoesNotExist:
        courses = None
    total_members = OrganizationMembers.objects.filter(organization_id=data.id).count()
    # webinar_count = course_extrainfo.objects.filter(course_type='1', display_org_with_default=org_sname).count()
    webinar_count = OrganizationCourse.objects.filter(organization_id=data.id).count()
    context = {
        "association_id": data.id,
        "assoc_name": data.name,
        "assoc_short_name": data.short_name,
        "assoc_logo": data.logo,
        "courses": courses,
        "total_members": total_members,
        "total_webinars": webinar_count,
        "grp_admin": grpstaff,
        "admin_courses": cid,
    }

    return render_to_response("associations/association_dashboard.html", context)


def course_usercount(userId):
    try:
        getDetails = CourseEnrollment.objects.filter(course_id=userId).count()
    except ObjectDoesNotExist:
        getDetails = "No data"

    return getDetails


def course_viewercount(userId):
    try:
        getDetails = StudentModule.objects.filter(
            course_id=userId, module_type="course"
        ).values("student_id")
        getDetails = len(getDetails)
    except ObjectDoesNotExist:
        getDetails = "No data"
    return getDetails


def organizationName(orgId):
    orgname = ""
    try:
        getDetails = Organization.objects.get(id=orgId)
        orgname = getDetails.name
    except ObjectDoesNotExist:
        getDetails = None

    return orgname


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET"])
def association_course_analytics(request, course_id):
    from opaque_keys.edx.locations import SlashSeparatedCourseKey
    from organizations.models import OrganizationCourse, OrganizationMembers
    from lms.djangoapps.reg_form.models import states

    gusr = request.user.id
    org_course = OrganizationCourse.objects.get(course_id=course_id)
    try:
        member_staff = OrganizationMembers.objects.get(
            user_id=gusr, organization_id=org_course.organization_id, is_admin="1"
        )
        # member_staff = OrganizationMembers.objects.get(user_id=gusr,organization_id=data.id)
    except ObjectDoesNotExist:
        member_staff = None

    try:
        sub_admin = Organization_sub_admins.objects.get(
            user_email=request.user.email,
            organization_id=org_course.organization_id,
            is_admin="1",
        )
    except ObjectDoesNotExist:
        sub_admin = None

    if member_staff is None:
        grpstaff = "0"
    else:
        grpstaff = "1"

    if sub_admin is None:
        sub_admin_staff = "0"
    else:
        sub_admin_staff = "1"

    def getState(userId):
        statename = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            statename = getDetails.rstate
        except ObjectDoesNotExist:
            getDetails = None

        return statename

    def getCity(userId):
        cityname = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            cityname = getDetails.rcity
        except ObjectDoesNotExist:
            getDetails = None

        return cityname

    def getViewerName(userId):
        vName = ""
        try:
            getDetails = UserProfile.objects.get(user_id=userId)
            vName = getDetails.name
        except ObjectDoesNotExist:
            getDetails = None

        return vName

    def getViewerEmail(userId):
        vEmail = ""
        try:
            getDetails = User.objects.get(id=userId)
            vEmail = getDetails.email
        except ObjectDoesNotExist:
            getDetails = None

        return vEmail

    if request.is_ajax():
        if "assoc_sub_admin" in request.GET:
            useremail = request.GET.get("emailid")
            assoc_id = request.GET.get("associd")
            course_id = course_id
            stateids = request.GET.get("stateids")
            test_list = json.loads(stateids)
            for i in range(0, len(test_list)):
                test_list[i] = int(test_list[i])
            gmember = Organization_sub_admins(
                user_email=useremail,
                organization_id=assoc_id,
                course_id=course_id,
                is_admin=1,
                active=1,
                state_ids=test_list,
            )
            gmember.save()
            data = {}
            data["status"] = 200
            data["msg"] = "Sub admin created success"
            return JsonResponse(data, status=200, safe=False)
        elif "courseid" in request.GET:

            cid = request.GET.get("courseid")
            cid = SlashSeparatedCourseKey.from_deprecated_string(cid)
            count = StudentModule.objects.filter(
                course_id=cid, module_type="video"
            ).count()
            crows = CourseEnrollment.objects.filter(course_id=cid)
            results = []
            for row in crows:
                user = {}
                user["name"] = getViewerName(row.user_id).encode("ASCII")
                user["state"] = getState(row.user_id).encode("ASCII")
                user["city"] = getCity(row.user_id).encode("ASCII")
                user["email"] = getViewerEmail(row.user_id).encode("ASCII")
                results.append(user)
            data = results
            return HttpResponse(json.dumps(data), content_type="application/json")
        elif "rangedate" in request.GET:
            from rg_instructor_analytics_log_collector.models import EnrollmentByDay

            if "course_id" != 0:
                cid = request.GET.get("course_id")

                cid = SlashSeparatedCourseKey.from_deprecated_string(cid)
                cdata = CourseOverview.objects.get(id=cid)
                fromdate = datetime.datetime.strptime(
                    request.GET.get("fromdate"), "%m/%d/%Y"
                )
                todate = datetime.datetime.strptime(
                    request.GET.get("todate"), "%m/%d/%Y"
                )
                data = []
                # below code to fetch enrolled users data
                cenrolls = (
                    EnrollmentByDay.objects.filter(
                        course=cid, day__range=(fromdate, todate)
                    )
                    .values("enrolled", "day")
                    .order_by("day")
                )

                log.info(u"stats--> %s", cenrolls)
                for spec in cenrolls:
                    course_data = {}
                    course_data["day"] = spec["day"].strftime("%m/%d/%Y")
                    course_data["total"] = spec["enrolled"]
                    data.append(course_data)
                # below code to fetch viewed user data
                vieweduser = StudentModule.objects.filter(
                    Q(course_id=cdata.id)
                    & Q(module_type="video")
                    & Q(created__gte=fromdate)
                    & Q(created__lte=todate)
                ).values("student_id")
                viewed_user_state_count = (
                    extrafields.objects.filter(user__id__in=vieweduser)
                    .exclude(rpincode=0)
                    .values("rstate")
                    .distinct()
                    .count()
                )
                viewed_user_country_count = (
                    extrafields.objects.filter(user__id__in=vieweduser)
                    .exclude(rpincode=0)
                    .values("rcountry")
                    .distinct()
                    .count()
                )
                viewed_user_pincode_count = (
                    extrafields.objects.filter(user__id__in=vieweduser)
                    .exclude(rpincode=0)
                    .values("rpincode")
                    .distinct()
                    .count()
                )
                # course_data['viewed_user_country_count'] = viewed_user_country_count
                # course_data['viewed_user_state_count'] = viewed_user_state_count
                # course_data['viewed_user_pincode_count'] = viewed_user_pincode_count
                return HttpResponse(
                    json.dumps(data, default=str), content_type="application/json"
                )

    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    cid = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        course = CourseOverview.objects.get(id=cid)
    except ObjectDoesNotExist:
        course = None
    course_start = course.start.strftime("%m/%d/%Y")
    course_enrollment_start = course.enrollment_start.strftime("%m/%d/%Y")
    course_end = course.end.strftime("%m/%d/%Y")

    try:
        enrolleduser = CourseEnrollment.objects.filter(
            course_id=cid, is_active=1
        ).count()
    except ObjectDoesNotExist:
        enrolleduser = "No data"

    try:
        viewers = StudentModule.objects.filter(
            course_id=cid, module_type="course"
        ).values("student_id")
        viewers = len(viewers)
    except ObjectDoesNotExist:
        viewers = "No data"
    data = Organization.objects.get(short_name=course.display_org_with_default)
    if sub_admin_staff == "1":
        state_id_list = []
        stateids = json.loads(sub_admin.state_ids)
        for i in range(0, len(stateids)):
            log.info("stateids %s", stateids[i])
            statename = states.objects.get(id=stateids[i])
            # state_id_list.append(int(stateids[i]))
            state_id_list.append(statename.name)
        cenrolls = CourseEnrollment.objects.filter(course_id=cid).values("user_id")
        specQset = (
            extrafields.objects.filter(user__id__in=cenrolls, rstate__in=state_id_list)
            .exclude(rpincode=0)
            .values("rstate")
            .annotate(dcount=Count("rstate"))
        )
        user_country_count = (
            extrafields.objects.filter(user__id__in=cenrolls, rstate__in=state_id_list)
            .exclude(rpincode=0)
            .values("rcountry")
            .annotate(dcount=Count("rcountry"))
            .distinct()
        )
        enrolleduserspecz = (
            extrafields.objects.filter(user__id__in=cenrolls, rstate__in=state_id_list)
            .exclude(specialization_id__isnull=True)
            .values("specialization_id")
            .annotate(dcount=Count("specialization_id"))
        )

        vieweduser = (
            StudentModule.objects.filter(course_id=cid).values("student_id").distinct()
        )
        courseviewers = (
            extrafields.objects.filter(
                user__id__in=vieweduser, rstate__in=state_id_list
            )
            .exclude(rpincode=0)
            .values("rstate")
            .annotate(dcount=Count("rstate"))
        )
        viewerspecz = (
            extrafields.objects.filter(
                user__id__in=vieweduser, rstate__in=state_id_list
            )
            .exclude(specialization_id__isnull=True)
            .values("specialization_id")
            .annotate(dcount=Count("specialization_id"))
        )
    else:
        cenrolls = CourseEnrollment.objects.filter(course_id=cid).values("user_id")
        specQset = (
            extrafields.objects.filter(user__id__in=cenrolls)
            .exclude(rpincode=0)
            .values("rstate")
            .annotate(dcount=Count("rstate"))
        )
        user_country_count = (
            extrafields.objects.filter(user__id__in=cenrolls)
            .exclude(rpincode=0)
            .values("rcountry")
            .annotate(dcount=Count("rcountry"))
            .distinct()
        )
        enrolleduserspecz = (
            extrafields.objects.filter(user__id__in=cenrolls)
            .exclude(specialization_id__isnull=True)
            .values("specialization_id")
            .annotate(dcount=Count("specialization_id"))
        )

        vieweduser = (
            StudentModule.objects.filter(course_id=cid).values("student_id").distinct()
        )
        courseviewers = (
            extrafields.objects.filter(user__id__in=vieweduser)
            .exclude(rpincode=0)
            .values("rstate")
            .annotate(dcount=Count("rstate"))
        )
        viewerspecz = (
            extrafields.objects.filter(user__id__in=vieweduser)
            .exclude(specialization_id__isnull=True)
            .values("specialization_id")
            .annotate(dcount=Count("specialization_id"))
        )

    context = {
        "association_id": data.id,
        "assoc_name": data.name,
        "assoc_short_name": data.short_name,
        "assoc_logo": data.logo,
        "courses": course,
        "total_enrolled": enrolleduser,
        "total_viewers": viewers,
        "enrolldata": specQset,
        "viewers": courseviewers,
        "country_count": user_country_count,
        "enrolleduserspecz": enrolleduserspecz,
        "viewerspecz": viewerspecz,
        "org_admin": grpstaff,
        "sub_admin": sub_admin_staff,
        "sadmin": sub_admin,
        "course_start": course_start,
        "course_enrollment_start": course_enrollment_start,
        "course_end": course_end,
    }

    return render_to_response("associations/association_course_analytics.html", context)


def export_csv(request, course_id, datatype):
    import csv
    from django.utils.encoding import smart_str

    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    cid = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=users.csv"
    writer = csv.writer(response, csv.excel)
    # BOM (optional...Excel needs it to open UTF-8 file properly)
    response.write(u"\ufeff".encode("utf8"))

    def getState(userId):
        statename = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            if getDetails.rstate != " ":
                statename = getDetails.rstate
            else:
                statename = "N/A"
        except ObjectDoesNotExist:
            getDetails = None

        return statename

    def getCity(userId):
        cityname = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            if getDetails.rcity != " ":
                cityname = getDetails.rcity
            else:
                cityname = "N/A"
        except ObjectDoesNotExist:
            getDetails = None

        return cityname

    def getspecialization(userId):
        from lms.djangoapps.specialization.views import specializationName

        speczname = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            specname = specializationName(getDetails.specialization_id)
            if specname != " ":
                speczname = specname
            else:
                speczname = "N/A"
        except ObjectDoesNotExist:
            speczname = "N/A"

        return speczname

    def getPincode(userId):
        pincode = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            pincode = getDetails.rpincode
        except ObjectDoesNotExist:
            getDetails = None
        return pincode

    def getmci(userId):
        mci = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId, user_type="dr")
            mci = getDetails.reg_num
        except ObjectDoesNotExist:
            mci = "N/A"
        return mci

    def getusertype(userId):
        u_type = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            utype = getDetails.user_type
            if utype == "dr":
                u_type = "Doctor"
            elif utype == "hc":
                u_type == "Healthcare Specialists"
            elif utype == "ms":
                u_type = "Medical Student"
            elif utype == "u":
                u_type = "User"
        except ObjectDoesNotExist:
            u_type = "N/A"
        return u_type

    def getphone(userId):
        phone = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            phone = getDetails.phone
        except ObjectDoesNotExist:
            phone = "N/A"
        return phone

    def getViewerName(userId):
        vName = ""
        try:
            getDetails = UserProfile.objects.get(user_id=userId)
            vName = getDetails.name
        except ObjectDoesNotExist:
            getDetails = None

        return vName

    def getemail(userId):
        vEmail = ""
        try:
            getDetails = User.objects.get(id=userId)
            vEmail = getDetails.email
        except ObjectDoesNotExist:
            getDetails = None

        return vEmail

    course_id = str(cid)
    course_number = course_id.split("+")
    user = request.user
    course_details = CourseOverview.objects.get(id=cid)
    course_exinfo = course_extrainfo.objects.get(course_id=cid)
    if (
        "stuckuser" in request.POST
        and user.is_staff
        or "stuckuser" in request.POST
        and user.email == "chetan.nirmalkar@alkem.com"
    ):
        emailids = request.POST.get("emailids")
        user_emails = emailids.split(",")
        email_list = []
        for i in range(0, len(user_emails)):
            email_list.append(str(user_emails[i]))
        user_list = []

        users = User.objects.filter(email__in=email_list)
        for assoc_user in users:
            user_ext = userdetails(assoc_user.id)
            user_data = {}
            user_data["Name"] = getViewerName(assoc_user.id)
            user_data["Emailid"] = assoc_user.email
            user_data["Mobile"] = user_ext.phone
            user_data["Type"] = getusertype(assoc_user.id)
            user_data["Regnum"] = user_ext.reg_num
            user_data["Specialization"] = getspecialization(assoc_user.id)
            user_data["State"] = user_ext.rstate
            user_data["City"] = user_ext.rcity
            user_data["Pincode"] = user_ext.rpincode
            user_data["Date joined"] = assoc_user.date_joined
            user_data["is_active"] = assoc_user.is_active
            user_list.append(user_data)
        # return user_list
        return JsonResponse(user_list, status=200, safe=False)
    elif user.is_staff:
        if "synapse" in course_id:
            writer.writerow(
                [
                    smart_str(u"Name"),
                    smart_str(u"Emailid"),
                    smart_str(u"Mobile"),
                    smart_str(u"Type"),
                    smart_str(u"MCI"),
                    smart_str(u"Specialization"),
                    smart_str(u"State"),
                    smart_str(u"City"),
                    smart_str(u"Pincode"),
                    smart_str(u"Date"),
                    smart_str(u"Video Watch time"),
                    smart_str(u"Is Active"),
                    smart_str(u"iadvl"),
                ]
            )
        elif (
            "Viatris" in course_id
            and str(course_details.start) > "2021-03-30 15:00:00"
            and datatype == "viewers"
        ):
            writer.writerow(
                [
                    smart_str(u"Name"),
                    smart_str(u"Emailid"),
                    smart_str(u"Mobile"),
                    smart_str(u"Type"),
                    smart_str(u"MCI"),
                    smart_str(u"Specialization"),
                    smart_str(u"State"),
                    smart_str(u"City"),
                    smart_str(u"Pincode"),
                    smart_str(u"pagein"),
                    smart_str(u"pageout"),
                    smart_str(u"Video Watch time"),
                    smart_str(u"Is Active"),
                ]
            )
        else:
            writer.writerow(
                [
                    smart_str(u"Userid"),
                    smart_str(u"Name"),
                    smart_str(u"Emailid"),
                    smart_str(u"Mobile"),
                    smart_str(u"Type"),
                    smart_str(u"MCI"),
                    smart_str(u"Specialization"),
                    smart_str(u"State"),
                    smart_str(u"City"),
                    smart_str(u"Pincode"),
                    smart_str(u"Date"),
                    smart_str(u"Video Watch time"),
                    smart_str(u"Is Active"),
                ]
            )
        if datatype == "enrolled":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_enrolledusers.csv"
            )
            crows = CourseEnrollment.objects.filter(course_id=cid)[:7000]
            if "synapse" in course_id:
                for row in crows:
                    try:
                        assoc_user = User.objects.get(id=row.user_id)
                        user_ext = userdetails(assoc_user.id)
                        writer.writerow(
                            [
                                smart_str(getViewerName(row.user_id)),
                                smart_str(assoc_user.email),
                                smart_str(user_ext.phone),
                                smart_str(user_ext.user_type),
                                smart_str(user_ext.reg_num),
                                smart_str(getspecialization(row.user_id)),
                                smart_str(user_ext.rstate),
                                smart_str(user_ext.rcity),
                                smart_str(user_ext.rpincode),
                                smart_str(row.created),
                                smart_str("N/A"),
                                smart_str(assoc_user.is_active),
                                smart_str(user_ext.user_extra_data),
                            ]
                        )
                    except ObjectDoesNotExist:
                        usernotfound = 0
            else:
                for row in crows:
                    try:
                        assoc_user = User.objects.get(id=row.user_id)
                        user_ext = userdetails(assoc_user.id)
                        writer.writerow(
                            [
                                smart_str(row.user_id),
                                smart_str(getViewerName(row.user_id)),
                                smart_str(getemail(row.user_id).encode("ASCII")),
                                smart_str(user_ext.phone),
                                smart_str(getusertype(row.user_id).encode("ASCII")),
                                smart_str(user_ext.reg_num),
                                smart_str(getspecialization(row.user_id)),
                                smart_str(user_ext.rstate),
                                smart_str(user_ext.rcity),
                                smart_str(user_ext.rpincode),
                                smart_str(row.created),
                                smart_str("N/A"),
                                smart_str(assoc_user.is_active),
                            ]
                        )
                    except ObjectDoesNotExist:
                        usernotfound = 0
        elif datatype == "viewers":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_viewers.csv"
            )
            if (
                "Viatris" in course_id
                and str(course_details.start) > "2021-03-30 15:00:00"
            ):
                webinar_time = int(course_exinfo.total_webinar_hours)
                course_start = course_details.start + datetime.timedelta(
                    hours=webinar_time
                )
                vrows = (
                    user_session_tracking.objects.filter(course_id=cid)
                    .values("user_id", "course_id")
                    .distinct()
                )

                for vrow in vrows:
                    userlogin = user_session_tracking.objects.filter(
                        course_id=vrow["course_id"], user_id=vrow["user_id"]
                    ).first()
                    userlogout = user_session_tracking.objects.filter(
                        course_id=vrow["course_id"], user_id=vrow["user_id"]
                    ).last()
                    assoc_user = User.objects.get(id=vrow["user_id"])
                    user_ext = userdetails(assoc_user.id)
                    datetimeFormat = "%Y-%m-%d %H:%M:%S"
                    intime = userlogin.pagein.astimezone(timezone("Asia/Kolkata"))

                    if userlogout.track_updated == 0:
                        new_out_time = userlogout.pageout + datetime.timedelta(
                            hours=webinar_time
                        )
                        outime = new_out_time.astimezone(timezone("Asia/Kolkata"))
                        total_time = str(new_out_time - userlogin.pagein)
                    else:
                        outime = userlogout.pageout.astimezone(timezone("Asia/Kolkata"))
                        total_time = str(userlogout.pageout - userlogin.pagein)
                    # log.info(u'time-> %s',total_time)

                    writer.writerow(
                        [
                            smart_str(getViewerName(vrow["user_id"])),
                            smart_str(getemail(vrow["user_id"]).encode("ASCII")),
                            smart_str(user_ext.phone),
                            smart_str(getusertype(vrow["user_id"]).encode("ASCII")),
                            smart_str(user_ext.reg_num),
                            smart_str(getspecialization(vrow["user_id"])),
                            smart_str(user_ext.rstate),
                            smart_str(user_ext.rcity),
                            smart_str(user_ext.rpincode),
                            smart_str(intime.strftime("%b %d, %Y %H:%M")),
                            smart_str(outime.strftime("%b %d, %Y %H:%M")),
                            smart_str(total_time.split(".")[0]),
                            smart_str(assoc_user.is_active),
                        ]
                    )
            else:
                vrows = (
                    StudentModule.objects.filter(course_id=cid, module_type="course")
                    .values("student_id", "created", "state")
                    .annotate(dcount=Count("student_id"))[:7000]
                )
                # vrows = StudentModule.objects.filter(course_id=cid,module_type='sequential').values('student_id','created','state').distinct()
                for vrow in vrows:
                    # log.info(u'vrow-> %s',vrow['student_id'])
                    assoc_user = User.objects.get(id=vrow["student_id"])
                    user_ext = userdetails(assoc_user.id)
                    writer.writerow(
                        [
                            smart_str(vrow["student_id"]),
                            smart_str(getViewerName(vrow["student_id"])),
                            smart_str(getemail(vrow["student_id"]).encode("ASCII")),
                            smart_str(user_ext.phone),
                            smart_str(getusertype(vrow["student_id"]).encode("ASCII")),
                            smart_str(user_ext.reg_num),
                            smart_str(getspecialization(vrow["student_id"])),
                            smart_str(user_ext.rstate),
                            smart_str(user_ext.rcity),
                            smart_str(user_ext.rpincode),
                            smart_str(vrow["created"]),
                            smart_str(vrow["state"]),
                            smart_str(assoc_user.is_active),
                        ]
                    )

    else:
        if "synapse" in course_id:
            writer.writerow(
                [
                    smart_str(u"Name"),
                    smart_str(u"Type"),
                    smart_str(u"MCI"),
                    smart_str(u"Specialization"),
                    smart_str(u"State"),
                    smart_str(u"City"),
                    smart_str(u"Pincode"),
                    smart_str(u"Date"),
                    smart_str(u"Video Watch time"),
                    smart_str(u"Is Active"),
                    smart_str(u"IADVL"),
                ]
            )
        else:
            writer.writerow(
                [
                    smart_str(u"Name"),
                    smart_str(u"Type"),
                    smart_str(u"MCI"),
                    smart_str(u"Specialization"),
                    smart_str(u"State"),
                    smart_str(u"City"),
                    smart_str(u"Pincode"),
                    smart_str(u"Date"),
                    smart_str(u"Video Watch time"),
                    smart_str(u"Is Active"),
                ]
            )
        if datatype == "enrolled":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_enrolledusers.csv"
            )
            crows = CourseEnrollment.objects.filter(course_id=cid)
            if "synapse" in course_id:
                for row in crows:
                    assoc_user = User.objects.get(id=row.user_id)
                    user_ext = userdetails(assoc_user.id)
                    writer.writerow(
                        [
                            smart_str(getViewerName(row.user_id)),
                            smart_str(getusertype(row.user_id).encode("ASCII")),
                            smart_str(user_ext.reg_num),
                            smart_str(getspecialization(row.user_id).encode("ASCII")),
                            smart_str(user_ext.rstate),
                            smart_str(user_ext.rcity),
                            smart_str(user_ext.rpincode),
                            smart_str(row.created),
                            smart_str("N/A"),
                            smart_str(assoc_user.is_active),
                            smart_str(user_ext.user_extra_data),
                        ]
                    )
            else:
                for row in crows:
                    assoc_user = User.objects.get(id=row.user_id)
                    user_ext = userdetails(assoc_user.id)
                    writer.writerow(
                        [
                            smart_str(getViewerName(row.user_id)),
                            smart_str(getusertype(row.user_id).encode("ASCII")),
                            smart_str(user_ext.reg_num),
                            smart_str(getspecialization(row.user_id).encode("ASCII")),
                            smart_str(user_ext.rstate),
                            smart_str(user_ext.rcity),
                            smart_str(user_ext.rpincode),
                            smart_str(row.created),
                            smart_str("N/A"),
                            smart_str(assoc_user.is_active),
                        ]
                    )
        elif datatype == "viewers":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_viewers.csv"
            )
            vrows = StudentModule.objects.filter(course_id=cid, module_type="course")[
                :7000
            ]
            for vrow in vrows:
                assoc_user = User.objects.get(id=vrow.student_id)
                user_ext = userdetails(assoc_user.id)
                writer.writerow(
                    [
                        smart_str(getViewerName(vrow.student_id)),
                        smart_str(getusertype(vrow.student_id).encode("ASCII")),
                        smart_str(user_ext.reg_num),
                        smart_str(getspecialization(vrow.student_id).encode("ASCII")),
                        smart_str(user_ext.rstate),
                        smart_str(user_ext.rcity),
                        smart_str(user_ext.rpincode),
                        smart_str(vrow.created),
                        smart_str(vrow.state),
                        smart_str(assoc_user.is_active),
                    ]
                )

    return response


export_csv.short_description = u"Export CSV"


def viatris_export_csv(request, course_id, datatype):
    import csv
    from django.utils.encoding import smart_str

    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    cid = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=users.csv"
    writer = csv.writer(response, csv.excel)
    # BOM (optional...Excel needs it to open UTF-8 file properly)
    response.write(u"\ufeff".encode("utf8"))

    def getspecialization(userId):
        from lms.djangoapps.specialization.views import specializationName

        speczname = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            specname = specializationName(getDetails.specialization_id)
            if specname != " ":
                speczname = specname
            else:
                speczname = "N/A"
        except ObjectDoesNotExist:
            speczname = "N/A"

        return speczname

    def getusertype(userId):
        u_type = ""
        try:
            getDetails = extrafields.objects.get(user_id=userId)
            utype = getDetails.user_type
            if utype == "dr":
                u_type = "Doctor"
            elif utype == "hc":
                u_type == "Healthcare Specialists"
            elif utype == "ms":
                u_type = "Medical Student"
            elif utype == "u":
                u_type = "User"
        except ObjectDoesNotExist:
            u_type = "N/A"
        return u_type

    course_id = str(cid)
    course_number = course_id.split("+")
    user = request.user
    course_details = CourseOverview.objects.get(id=cid)
    course_exinfo = course_extrainfo.objects.get(course_id=cid)
    if "stuckuser" in request.POST and user.is_staff or "stuckuser" in request.POST:
        emailids = request.POST.get("emailids")
        user_emails = emailids.split(",")
        email_list = []
        for i in range(0, len(user_emails)):
            email_list.append(str(user_emails[i]))
        user_list = []

        users = User.objects.filter(email__in=email_list)
        for assoc_user in users:
            user_ext = userdetails(assoc_user.id)
            user_data = {}
            user_data["Name"] = getViewerName(assoc_user.id)
            user_data["Emailid"] = assoc_user.email
            user_data["Mobile"] = user_ext.phone
            user_data["Type"] = getusertype(assoc_user.id)
            user_data["Regnum"] = user_ext.reg_num
            user_data["Specialization"] = getspecialization(assoc_user.id)
            user_data["State"] = user_ext.rstate
            user_data["City"] = user_ext.rcity
            user_data["Pincode"] = user_ext.rpincode
            user_data["Date joined"] = assoc_user.date_joined
            user_data["is_active"] = assoc_user.is_active
            user_list.append(user_data)
        # return user_list
        return JsonResponse(user_list, status=200, safe=False)
    elif user.is_staff:

        writer.writerow(
            [
                smart_str(u"Userid"),
                smart_str(u"Firstname"),
                smart_str(u"Last Name"),
                smart_str(u"Emailid"),
                smart_str(u"Specialization"),
                smart_str(u"Country"),
                smart_str(u"Organization name"),
                smart_str(u"Organization City"),
                smart_str(u"Organization Pincode"),
                smart_str(u"Organization address"),
                smart_str(u"National Laws"),
                smart_str(u"Privacy Notice"),
                smart_str(u"EMAS newsletter"),
                smart_str(u"Date joined"),
                smart_str(u"Is Verified"),
                smart_str(u"profession Reg_num"),
            ]
        )
        if datatype == "enrolled":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_enrolledusers.csv"
            )
            crows = CourseEnrollment.objects.filter(course_id=cid, user_id__gte=190000)[
                :7000
            ]
            for row in crows:
                log.info("id--> %s", row.user_id)
                try:
                    assoc_user = User.objects.get(id=row.user_id)
                    user_detail = getuserfullprofile(row.user_id)
                    user_ext = userdetails(assoc_user.id)
                    extd = ast.literal_eval(user_ext.user_extra_data)
                    ext = json.dumps(extd)
                    ext = eval(ext)
                    fname = ext.get("fname")
                    if fname:
                        fname = ext["fname"]
                    else:
                        fname = user_detail.name

                    lname = ext.get("lname")
                    if lname:
                        lname = ext["lname"]
                    else:
                        lname = "N/A"

                    ogname = ext.get("ogname")
                    if ogname:
                        ogname = ext["ogname"]
                    else:
                        ogname = "N/A"

                    org_address = ext.get("org_address")
                    if org_address:
                        org_address = ext["org_address"]
                    else:
                        org_address = "N/A"

                    nationallaws = ext.get("nationallaws")
                    if nationallaws:
                        nationallaws = ext["nationallaws"]
                    else:
                        nationallaws = "N/A"

                    dataprotection = ext.get("dataprotection")
                    if dataprotection:
                        dataprotection = ext["dataprotection"]
                    else:
                        dataprotection = "N/A"

                    iagree = ext.get("iagree")
                    if iagree:
                        iagree = ext["iagree"]
                    else:
                        iagree = "N/A"

                    profession_reg_num = ext.get("profession_reg_num")
                    if profession_reg_num:
                        profession_reg_num = ext["profession_reg_num"]
                    else:
                        profession_reg_num = "N/A"

                    writer.writerow(
                        [
                            smart_str(row.user_id),
                            smart_str(fname),
                            smart_str(lname),
                            smart_str(assoc_user.email),
                            smart_str(getspecialization(row.user_id)),
                            smart_str(user_ext.rcountry),
                            smart_str(ogname),
                            smart_str(org_address),
                            smart_str(user_ext.rcity),
                            smart_str(user_ext.rpincode),
                            smart_str(nationallaws),
                            smart_str(dataprotection),
                            smart_str(iagree),
                            smart_str(row.created),
                            smart_str(assoc_user.is_active),
                            smart_str(profession_reg_num),
                        ]
                    )
                except ObjectDoesNotExist:
                    usernotfound = 0
        elif datatype == "viewers":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_viewers.csv"
            )
            vrows = (
                StudentModule.objects.filter(
                    course_id=cid, module_type="course", student_id__gte=195590
                )
                .values("student_id", "created", "state")
                .annotate(dcount=Count("student_id"))[:7000]
            )
            # vrows = StudentModule.objects.filter(course_id=cid,module_type='sequential').values('student_id','created','state').distinct()
            for vrow in vrows:
                log.info("id--> %s", vrow["student_id"])
                assoc_user = User.objects.get(id=vrow["student_id"])
                user_ext = userdetails(assoc_user.id)
                user_detail = getuserfullprofile(assoc_user.id)
                extd = ast.literal_eval(user_ext.user_extra_data)
                ext = json.dumps(extd)
                ext = eval(ext)
                fname = ext.get("fname")
                if fname:
                    fname = ext["fname"]
                else:
                    fname = user_detail.name

                lname = ext.get("lname")
                if lname:
                    lname = ext["lname"]
                else:
                    lname = "N/A"

                ogname = ext.get("ogname")
                if ogname:
                    ogname = ext["ogname"]
                else:
                    ogname = "N/A"

                org_address = ext.get("org_address")
                if org_address:
                    org_address = ext["org_address"]
                else:
                    org_address = "N/A"

                nationallaws = ext.get("nationallaws")
                if nationallaws:
                    nationallaws = ext["nationallaws"]
                else:
                    nationallaws = "N/A"

                dataprotection = ext.get("dataprotection")
                if dataprotection:
                    dataprotection = ext["dataprotection"]
                else:
                    dataprotection = "N/A"

                iagree = ext.get("iagree")
                if iagree:
                    iagree = ext["iagree"]
                else:
                    iagree = "N/A"

                profession_reg_num = ext.get("profession_reg_num")
                if profession_reg_num:
                    profession_reg_num = ext["profession_reg_num"]
                else:
                    profession_reg_num = "N/A"
                writer.writerow(
                    [
                        smart_str(vrow["student_id"]),
                        smart_str(fname),
                        smart_str(lname),
                        smart_str(assoc_user.email),
                        smart_str(getspecialization(vrow["student_id"])),
                        smart_str(user_ext.rcountry),
                        smart_str(ogname),
                        smart_str(org_address),
                        smart_str(user_ext.rcity),
                        smart_str(user_ext.rpincode),
                        smart_str(nationallaws),
                        smart_str(dataprotection),
                        smart_str(vrow["created"]),
                        smart_str(assoc_user.is_active),
                        smart_str(profession_reg_num),
                    ]
                )
    else:
        writer.writerow(
            [
                smart_str(u"Firstname"),
                smart_str(u"Last Name"),
                smart_str(u"Emailid"),
                smart_str(u"Specialization"),
                smart_str(u"Country"),
                smart_str(u"Organization name"),
                smart_str(u"Organization City"),
                smart_str(u"Organization Pincode"),
                smart_str(u"Organization address"),
                smart_str(u"National Laws"),
                smart_str(u"Privacy Notice"),
                smart_str(u"Date joined"),
                smart_str(u"Is Verified"),
                smart_str(u"profession Reg_num"),
            ]
        )
        if datatype == "enrolled":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_enrolledusers.csv"
            )
            crows = CourseEnrollment.objects.filter(course_id=cid)
            for row in crows:
                assoc_user = User.objects.get(id=row.user_id)
                user_ext = userdetails(assoc_user.id)
                extra_field_data = json.load(user_ext.user_extra_data)
                extd = ast.literal_eval(user_ext.user_extra_data)
                ext = json.dumps(extd)
                ext = eval(ext)
                fname = ext.get("fname")
                if fname:
                    fname = ext["fname"]
                else:
                    fname = user_detail.name

                lname = ext.get("lname")
                if lname:
                    lname = ext["lname"]
                else:
                    lname = "N/A"

                ogname = ext.get("ogname")
                if ogname:
                    ogname = ext["ogname"]
                else:
                    ogname = "N/A"

                org_address = ext.get("org_address")
                if org_address:
                    org_address = ext["org_address"]
                else:
                    org_address = "N/A"

                nationallaws = ext.get("nationallaws")
                if nationallaws:
                    nationallaws = ext["nationallaws"]
                else:
                    nationallaws = "N/A"

                dataprotection = ext.get("dataprotection")
                if dataprotection:
                    dataprotection = ext["dataprotection"]
                else:
                    dataprotection = "N/A"

                iagree = ext.get("iagree")
                if iagree:
                    iagree = ext["iagree"]
                else:
                    iagree = "N/A"

                profession_reg_num = ext.get("profession_reg_num")
                if profession_reg_num:
                    profession_reg_num = ext["profession_reg_num"]
                else:
                    profession_reg_num = "N/A"
                writer.writerow(
                    [
                        smart_str(row.user_id),
                        smart_str(fname),
                        smart_str(lname),
                        smart_str(assoc_user.email),
                        smart_str(getspecialization(row.user_id)),
                        smart_str(user_ext.rcountry),
                        smart_str(ogname),
                        smart_str(org_address),
                        smart_str(user_ext.rcity),
                        smart_str(user_ext.rpincode),
                        smart_str(nationallaws),
                        smart_str(dataprotection),
                        smart_str(row.created),
                        smart_str(assoc_user.is_active),
                        smart_str(profession_reg_num),
                    ]
                )
        elif datatype == "viewers":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_viewers.csv"
            )
            vrows = StudentModule.objects.filter(course_id=cid, module_type="course")[
                :7000
            ]
            for vrow in vrows:
                assoc_user = User.objects.get(id=vrow.student_id)
                user_ext = userdetails(assoc_user.id)
                extra_field_data = json.load(user_ext.user_extra_data)
                extd = ast.literal_eval(user_ext.user_extra_data)
                ext = json.dumps(extd)
                ext = eval(ext)
                dataprotection = ext.get("dataprotection")
                if dataprotection:
                    dataprotection = ext["dataprotection"]
                else:
                    dataprotection = "N/A"

                profession_reg_num = ext.get("profession_reg_num")
                if profession_reg_num:
                    profession_reg_num = ext["profession_reg_num"]
                else:
                    profession_reg_num = "N/A"
                writer.writerow(
                    [
                        smart_str(vrow.student_id),
                        smart_str(ext["fname"]),
                        smart_str(ext["lname"]),
                        smart_str(assoc_user.email),
                        smart_str(getspecialization(row.student_id)),
                        smart_str(user_ext.rcountry),
                        smart_str(ext["ogname"]),
                        smart_str(ext["org_address"]),
                        smart_str(user_ext.rcity),
                        smart_str(user_ext.rpincode),
                        smart_str(ext["nationallaws"]),
                        smart_str(dataprotection),
                        smart_str(row.created),
                        smart_str(assoc_user.is_active),
                        smart_str(profession_reg_num),
                    ]
                )
    return response


export_csv.short_description = u"Export CSV"


def autojoin_org(userid, course_id, email):

    from organizations.models import OrganizationMembers
    from organizations.models import OrganizationCourse

    org_id = OrganizationCourse.objects.get(course_id=course_id)

    gmember = OrganizationMembers(
        user_id=userid, organization_id=org_id.organization_id, user_email=email
    )
    gmember.save()


def assoc_join(userid, org_id, email):
    from organizations.models import OrganizationMembers

    data = Organization.objects.get(short_name=org_id)
    gmember = OrganizationMembers(
        user_id=userid, organization_id=data.id, user_email=email
    )
    gmember.save()


def check_domain_in_usermail(sponsoring_companyname="lupin"):
    from organizations.models import SponsoringCompany

    try:
        sname = SponsoringCompany.objects.filter(name=sponsoring_companyname)
        found = 1
    except ObjectDoesNotExist:
        found = 0
    return found


def search_list(request):
    if request.is_ajax():
        if request.method == "GET":
            if "email_validation" in request.GET:
                log.info(u"reqs--> %s", request.__dict__)
                emailid = request.GET.get("emailid")
                msg = {}
                try:
                    getDetails = User.objects.get(email=emailid)
                    msg["validity"] = "valid"
                    msg["status"] = 200
                except ObjectDoesNotExist:
                    msg["validity"] = "invalid"
                    msg["status"] = 400
                return JsonResponse(msg, status=200, safe=False)
            elif "mobile_validation" in request.GET:
                msg = {}
                mobile = request.GET.get("mobile")
                log.info(u"mobile-> %s", mobile)
                try:
                    user_multi_account = extrafields.objects.filter(
                        phone=mobile
                    ).count()
                    log.info(u"useraccount-> %s", user_multi_account)
                    msg["user_multi_account"] = user_multi_account
                    if user_multi_account > 1:
                        user_emails = extrafields.objects.filter(phone=mobile)
                        emailids = []
                        for userid in user_emails:
                            emailid = User.objects.get(id=userid.user_id)
                            emailids.append(emailid.email)
                        log.info(u"emailids-> %s", emailids)
                        msg["emailids"] = emailids
                        msg["status"] = 200
                except ObjectDoesNotExist:
                    msg["validity"] = "invalid"
                    msg["status"] = 400
                return JsonResponse(msg, status=200, safe=False)
            elif "trackingadd" in request.GET:
                usr = request.user.id
                course_id = request.GET.get("course_id")
                course_name = request.GET.get("coursename")
                module_name = request.GET.get("moduleName")
                sub_module_name = request.GET.get("submoduleName")
                usession = user_session_tracking(
                    user_id=usr,
                    course_id=course_id,
                    course_name=course_name,
                    module_name=module_name,
                    sub_module_name=sub_module_name,
                )
                usession.save()
                msg = {}
                if usession:
                    msg["user_session_added"] = "succesful"
                else:
                    msg["user_session_added"] = "unsuccesful"
                return JsonResponse(msg, status=200, safe=False)
            elif "trackingupdate" in request.GET:
                usr = request.user.id
                course_id = request.GET.get("course_id")
                sub_module_name = request.GET.get("submoduleName")
                logout = datetime.datetime.now(UTC)
                get_tracking = user_session_tracking.objects.filter(
                    course_id=course_id,
                    user_id=usr,
                    sub_module_name=sub_module_name,
                    track_updated=0,
                ).update(pageout=logout, track_updated=1)

                msg = {}
                if get_tracking:
                    msg["user_session_added"] = "succesful"
                else:
                    msg["user_session_added"] = "unsuccesful"
                return JsonResponse(msg, status=200, safe=False)
            else:
                search_term = request.GET.get("search_term")

                results = CourseOverview.objects.filter(
                    Q(display_name__icontains=search_term)
                    | Q(display_org_with_default__icontains=search_term)
                ).values("id", "display_name")
                # log.info("result-> %s",results)
                result_dict = []

            for result in results:
                search_result = {}
                search_result["course_name"] = result["display_name"]
                search_result["course_id"] = str(result["id"])
                result_dict.append(search_result)
            # qs_json = serializers.serialize('json', results)
            return HttpResponse(
                json.dumps(result_dict), content_type="application/json"
            )
    context = {"search_term": "Result"}

    return render_to_response("forum/search_result.html", context)


# reminder user lists


@view_auth_classes(is_authenticated=False)
class reminder_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        from lms.djangoapps.reg_form.views import get_authuser

        coursetype = course_extrainfo.objects.filter(course_type=1)
        association_list = []
        for courseid in coursetype:
            course_id = CourseKey.from_string(courseid.course_id)
            enrolled_users_lists = CourseEnrollment.objects.filter(course_id=course_id)
            for userid in enrolled_users_lists:
                log.info(u"user->course %s,%s", userid.user_id, userid.course_id)
                try:
                    non_passed_users = PersistentCourseGrade.objects.get(
                        user_id=userid.user_id,
                        course_id=userid.course_id,
                        letter_grade="",
                    )

                    user_lastlogin = User.objects.get(id=non_passed_users.user_id)
                    if user_lastlogin.last_login is not None:
                        diffdate = (
                            datetime.datetime.now(UTC) - user_lastlogin.last_login
                        )
                        association_dict = {}
                        if diffdate.days >= 3:
                            association_dict["email"] = user_lastlogin.email
                            association_dict["days"] = diffdate.days
                            association_list.append(association_dict)
                except ObjectDoesNotExist:
                    non_passed_users = "n/a"

        network_list = []
        network_dict = {}
        network_dict["name"] = "Enrolled Users"
        network_dict["value"] = association_list
        network_list.append(network_dict)
        return JsonResponse(network_list, status=200, safe=False)


# association api's start


@view_auth_classes(is_authenticated=False)
class in_network_with_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        associations_list = Organization.objects.filter(
            active=1, homepage_in_network_with=1
        )
        association_list = []
        if associations_list:
            for assoc in associations_list:
                # img_link = assoc.logo.split('https://s3-ap-southeast-1.amazonaws.com/')
                association_dict = {}
                association_dict["short_name"] = assoc.short_name
                association_dict["logo"] = str(assoc.logo)
                association_list.append(association_dict)
        else:
            association_list = []

        network_list = []
        network_dict = {}
        network_dict["name"] = "Network"
        network_dict["value"] = association_list
        network_list.append(network_dict)
        return JsonResponse(network_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class topic_course_lect_count_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        cat_course_count = (
            course_extrainfo.objects.exclude(category="")
            .values("category")
            .annotate(ccount=Count("category"))
            .filter(ccount__gte=1)
            .order_by("-ccount")[:8]
        )
        categoryid = []
        for catid in cat_course_count:
            categoryid.append(catid["category"])
        categories_list = categories.objects.filter(pk__in=categoryid).values()

        category_list = []
        if categories_list:
            for category in categories_list:
                courses_count = category_courses_count(category["id"])
                lectures_count = category_lectures_count(category["id"])
                case_studies_count = category_casestudies_count(category["id"])
                category_dict = {}
                category_dict["name"] = category["topic_name"]
                category_dict["topic_url"] = (
                    "https://learn.docmode.org/subjects/" + category["topic_short_name"]
                )
                if courses_count:
                    category_dict["courses_count"] = courses_count[0]["ccount"]
                if lectures_count:
                    category_dict["lectures_count"] = lectures_count[0]["ccount"]
                if case_studies_count:
                    category_dict["case_studies_count"] = case_studies_count[0][
                        "ccount"
                    ]
                category_list.append(category_dict)
        else:
            association_list = []
        return JsonResponse(category_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class partners_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        user = request.user
        associations_list = Organization.objects.filter(marketing_display=1).order_by(
            "name"
        )

        association_list = []
        if associations_list:
            for assoc in associations_list:
                # img_link = assoc.logo.split('https://s3-ap-southeast-1.amazonaws.com/')
                association_dict = {}
                association_dict["name"] = assoc.name
                association_dict["short_name"] = assoc.short_name
                association_dict["logo"] = str(assoc.logo)
                # association_dict['assoc_detail_ur'] = 'https://learn.docmode.org/'+assoc.short_name+'/'
                association_list.append(association_dict)
        else:
            association_list = []

        network_list = []
        network_dict = {}
        network_dict["name"] = "Associations"
        network_dict["value"] = association_list
        network_list.append(network_dict)
        return JsonResponse(network_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class partner_details_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        user = request.user
        requested_params = self.request.query_params.copy()
        org = self.kwargs["association_about"]
        association = Organization.objects.get(short_name=org, active=1)

        if association:
            association_list = []
            association_dict = {}
            association_dict["name"] = association.name
            association_dict["descrption"] = association.description
            association_dict["logo"] = str(association.logo)
            association_dict["org_promo_video"] = association.org_promo_video
            if user.is_authenticated():
                if user.is_staff:
                    association_dict["is_staff"] = "staff"
                    association_dict["dashboard_url"] = (
                        "https://learn.docmode.org/dashboard/"
                        + association.short_name
                        + "/"
                    )
                else:
                    try:
                        assoc_member_admin = OrganizationMembers.objects.get(
                            organization_id=association.id, is_admin=1, user_id=user.id
                        )
                        association_dict["is_staff"] = "staff"
                        association_dict["dashboard_url"] = (
                            "https://learn.docmode.org/dashboard/"
                            + association.short_name
                            + "/"
                        )
                    except ObjectDoesNotExist:
                        association_dict["is_staff"] = "No"
            else:
                association_dict["is_staff"] = "No"

            try:
                slider_images = OrganizationSlider.objects.get(
                    organization_id=association.id
                )
                association_dict["slider_images"] = slider_images.image_s3_urls
            except ObjectDoesNotExist:
                slider_images = None
                association_dict[
                    "slider_images"
                ] = "http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg"

            # slider_images = OrganizationSlider.objects.get(organization_id=association.id)
            # if slider_images:
            #     association_dict['slider_images'] = slider_images.image_s3_urls
            # else:
            #     association_dict['slider_images'] = 'http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg'

            courses = (
                CourseOverview.objects.all()
                .filter(display_org_with_default=org, catalog_visibility="both")
                .order_by("start")[::-1]
            )
            assoc_course_list = []
            for course in courses:
                assoc_course_dict = {}
                course_id = str(course.id)
                course_extra_info = course_extrainfo.objects.get(course_id=course.id)
                # log.info(u"query %s",course.id)
                data = association.name
                info = (data[:8] + "..") if len(data) > 10 else data
                course_name = (
                    (course.display_name[:40] + "..")
                    if len(course.display_name) > 50
                    else course.display_name
                )
                assoc_course_dict["course_title"] = course_name
                assoc_course_dict["org"] = info
                assoc_course_dict["media"] = course.course_image_url
                if course_extra_info:
                    assoc_course_dict["wp_url"] = (
                        "https://docmode.org/" + course_extra_info.course_seo_url
                    )

                    if course_extra_info.course_type == "1":
                        assoc_course_dict["course_type"] = "Course"
                    elif course_extra_info.course_type == "2":
                        assoc_course_dict["course_type"] = "Lecture"
                    else:
                        assoc_course_dict["course_type"] = "Case Study"
                assoc_course_dict["start"] = course.start.strftime("%b %d, %Y ")
                assoc_course_list.append(assoc_course_dict)
            association_list.append(association_dict)
            association_list.append(assoc_course_list)
            return JsonResponse(association_list, status=200, safe=False)
        else:
            association_list = []
            association_dict = {}
            association_dict["error"] = "Invalid association name"
            association_list.append(association_dict)
            return JsonResponse(
                association_list, status=status.HTTP_400_BAD_REQUEST, safe=False
            )


def get_assoc(org):
    try:
        tassoc = Organization.objects.get(short_name=org, active=1)
        assoc = tassoc.id
    except ObjectDoesNotExist:
        assoc = "Invalid"
    return assoc


def get_user(email):
    try:
        wpuser = User.objects.get(email=email)
        wpuser = wpuser.id
    except ObjectDoesNotExist:
        wpuser = "Invalid"
    return wpuser


def get_staff(email):
    try:
        staff = User.objects.get(email=email)
        staff = staff.is_staff
    except ObjectDoesNotExist:
        staff = 0
    return staff


@view_auth_classes(is_authenticated=False)
class wp_partner_admin_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        requested_params = self.request.query_params.copy()
        org = self.kwargs["association_about"]
        assoc = get_assoc(org)
        wpusername = self.kwargs["emailid"]
        user_details = get_user(wpusername)
        log.info(u"user->%s", wpusername)
        log.info(u"user->details %s", user_details)
        try:
            assoc_member_admin = OrganizationMembers.objects.get(
                organization_id=assoc, is_admin=1, user_id=user_details
            )
            is_admin = "Yes"
        except ObjectDoesNotExist:
            is_admin = "No"

        ustaff = get_staff(wpusername)
        association_list = []
        association_dict = {}
        association_dict["assoc_admin"] = is_admin
        association_dict["staff"] = ustaff
        association_list.append(association_dict)
        return JsonResponse(association_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class topics_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        topics_list = categories.objects.all().order_by("topic_name")
        # .annotate(ccount=Count('active'))

        topic_list = []
        if topics_list:
            for topic in topics_list:
                # img_link = assoc.logo.split('https://s3-ap-southeast-1.amazonaws.com/')
                topic_dict = {}
                topic_dict["name"] = topic.topic_name
                topic_dict["short_name"] = topic.topic_short_name
                topic_dict["image_url"] = str(topic.topic_image)
                topic_dict["url"] = "https://docmode.org/" + str(topic.topic_short_name)
                topic_list.append(topic_dict)
        else:
            association_list = []

        network_list = []
        network_dict = {}
        network_dict["name"] = "Topics"
        network_dict["value"] = topic_list
        network_list.append(network_dict)
        return JsonResponse(network_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class specializations_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        speclzns = specializations.objects.all().order_by("name")

        speclzns_list = []
        if speclzns:
            for specz in speclzns:
                # img_link = assoc.logo.split('https://s3-ap-southeast-1.amazonaws.com/')
                specz_dict = {}
                specz_dict["id"] = specz.id
                specz_dict["name"] = specz.name
                specz_dict["image"] = specz.image
                speclzns_list.append(specz_dict)
        else:
            speclzn_list = []

        network_list = []
        network_dict = {}
        network_dict["name"] = "Specialization"
        network_dict["value"] = speclzns_list
        network_list.append(network_dict)
        return JsonResponse(network_list, status=200, safe=False)


def get_effective_user(requesting_user, target_username):
    """
    Get the user we want to view information on behalf of.
    """
    if target_username == requesting_user.username:
        return requesting_user
    elif target_username == "":
        return AnonymousUser()
    elif can_view_courses_for_username(requesting_user, target_username):
        return User.objects.get(username=target_username)
    else:
        raise PermissionDenied()


def course_detail(request, username, course_key):
    """
    Return a single course identified by `course_key`.

    The course must be visible to the user identified by `username` and the
    logged-in user should have permission to view courses available to that
    user.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user `requesting_user would like to be identified as.
        course_key (CourseKey): Identifies the course of interest

    Return value:
        `CourseOverview` object representing the requested course
    """
    user = get_effective_user(request.user, username)
    from lms.djangoapps.commerce.utils import EcommerceService
    from lms.djangoapps.add_manager.models import associations_ad_manager

    obj = EcommerceService()
    from course_modes.models import CourseMode

    course_sku = CourseMode.objects.filter(course_id=course_key)
    if course_sku:
        sku = course_sku[0].sku
        payment = obj.get_checkout_page_url(sku)
        course_price = course_sku[0].min_price
    else:
        payment = ""
        course_price = "Free"
    datas = get_course_overview_with_access(
        user,
        get_permission_for_course_about(),
        course_key,
    )

    course_org = CourseOverview.objects.get(id=course_key)
    association = Organization.objects.get(
        short_name=course_org.display_org_with_default, active=1
    )
    courses = (
        CourseOverview.objects.all()
        .filter(display_org_with_default=course_org.org, catalog_visibility="both")
        .order_by("start")[::-1]
    )
    course_disclaimer_list = []
    try:
        course_key = str(course_org.id)
        log.info(u"coursek-> %s", course_org.id)
        ad_disclaimer = associations_ad_manager.objects.get(course_id=course_org.id)
        dsclmr = ad_disclaimer.disclaimer
        disclaimers = dsclmr.split("|")
        count = 0
        for item in disclaimers:
            # course_disclaimer_dict = {}
            # course_disclaimer_dict['disclaimer'+ str(count)] = disclaimers[count]
            course_disclaimer_list.append(disclaimers[count])
            count += 1
        # log.info(u'coursed-> %s',course_disclaimer_list)
    except ObjectDoesNotExist:
        ad_disclaimer = "n/a"

    assoc_course_list = []
    for course in courses:
        assoc_course_dict = {}
        course_id = str(course.id)
        course_extra_info = course_extrainfo.objects.get(course_id=course.id)
        data = association.name
        info = (data[:8] + "..") if len(data) > 10 else data
        course_name = (
            (course.display_name[:40] + "..")
            if len(course.display_name) > 50
            else course.display_name
        )
        assoc_course_dict["course_title"] = course_name
        assoc_course_dict["org"] = info
        assoc_course_dict["media"] = course.course_image_url
        if course_extra_info:
            assoc_course_dict["wp_url"] = (
                "https://docmode.org/" + course_extra_info.course_seo_url
            )

            if course_extra_info.course_type == "1":
                assoc_course_dict["course_type"] = "Course"
            elif course_extra_info.course_type == "2":
                assoc_course_dict["course_type"] = "Lecture"
            else:
                assoc_course_dict["course_type"] = "Case Study"
        assoc_course_dict["start"] = course.start.strftime("%b %d, %Y ")
        assoc_course_list.append(assoc_course_dict)

    datas.other_courses = assoc_course_list
    datas.disclaimer = course_disclaimer_list
    datas.payment_url = payment
    datas.course_price = course_price
    datas.save()
    return datas


@view_auth_classes(is_authenticated=False)
class Wp_CourseDetailView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * overview: A possibly verbose HTML textual description of the course.
            Note: this field is only included in the Course Detail view, not
            the Course List view.
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self

        Deprecated fields:

        * blocks_url: Used to fetch the course blocks
        * course_id: Course key (use 'id' instead)

    **Parameters:**

        username (optional):
            The username of the specified user for whom the course data
            is being accessed. The username is not only required if the API is
            requested by an Anonymous user.

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.

        Example response:

            {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                    "course_image": {
                        "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                        "name": "Course Image"
                    }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "overview: "<p>A verbose description of the course.</p>"
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp",
                "pacing": "instructor"
            }
    """

    serializer_class = CourseDetailSerializer

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        requested_params = self.request.query_params.copy()
        course_title = self.kwargs["course_title"]
        # course_det = course_title.replace("-"," ")
        # log.info(u" course title %s", course_title)
        course_key = course_extrainfo.objects.get(course_seo_url=course_title)
        # course_key = CourseOverview.objects.get(display_name__icontains=course_det)
        # log.info(u" course key %s", course_key.__dict__)
        # log.info(u" course id %s", course_key)
        # for courseid in course_key:
        requested_params.update({"course_key": course_key.course_id})
        form = CourseDetailGetForm(
            requested_params, initial={"requesting_user": self.request.user}
        )
        if not form.is_valid():
            raise ValidationError(form.errors)

        return course_detail(
            self.request,
            form.cleaned_data["username"],
            form.cleaned_data["course_key"],
        )


def custom_course_detail(request, username, course_key):
    """
    Return a single course identified by `course_key`.

    The course must be visible to the user identified by `username` and the
    logged-in user should have permission to view courses available to that
    user.

    Arguments:
        request (HTTPRequest):
            Used to identify the logged-in user and to instantiate the course
            module to retrieve the course about description
        username (string):
            The name of the user `requesting_user would like to be identified as.
        course_key (CourseKey): Identifies the course of interest

    Return value:
        `CourseOverview` object representing the requested course
    """
    user = get_effective_user(request.user, username)
    from lms.djangoapps.commerce.utils import EcommerceService
    from lms.djangoapps.add_manager.models import associations_ad_manager

    obj = EcommerceService()
    from course_modes.models import CourseMode

    course_sku = CourseMode.objects.filter(course_id=course_key)
    if course_sku:
        sku = course_sku[0].sku
        payment = obj.get_checkout_page_url(sku)
        course_price = course_sku[0].min_price
    else:
        payment = ""
        course_price = "Free"
    datas = get_course_overview_with_access(
        user,
        get_permission_for_course_about(),
        course_key,
    )

    course_org = CourseOverview.objects.get(id=course_key)
    association = Organization.objects.get(
        short_name=course_org.display_org_with_default, active=1
    )
    courses = (
        CourseOverview.objects.all()
        .filter(display_org_with_default=course_org.org, catalog_visibility="both")
        .order_by("start")[::-1]
    )
    course_extradata = course_extrainfo.objects.get(course_id=course_org.id)
    topic_name = categories.objects.get(id=course_extradata.category)
    instructor_list = []
    course_id = course_org.id
    instructor_data = CourseAccessRole.objects.filter(
        course_id=course_id, role="instructor"
    )
    for instructor in instructor_data:
        user = User.objects.get(id=instructor.user_id)
        if "docmode" not in user.email:
            user_detail = getuserfullprofile(instructor.user_id)
            user_extra_data = userdetails(instructor.user_id)
            profile_image = get_profile_image_urls_for_user(user, request=None)
            prof_img = profile_image["large"].split("?v")

            instructor_dict = {}
            instructor_dict["name"] = user_detail.name
            instructor_dict["education"] = user_extra_data.education
            instructor_dict["bio"] = user_extra_data.user_long_description
            instructor_dict["profile_image"] = "https://learn.docmode.org" + prof_img[0]
            instructor_list.append(instructor_dict)

    # datas.other_courses = assoc_course_list
    # datas.disclaimer = instructor_list
    datas.topic_name = topic_name.topic_name
    datas.instructors = instructor_list
    datas.total_enrolled_users = course_usercount(course_id)
    # datas.payment_url = payment
    # datas.course_price = course_price
    datas.save()
    return datas


@view_auth_classes(is_authenticated=False)
class custom_CourseDetailView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * overview: A possibly verbose HTML textual description of the course.
            Note: this field is only included in the Course Detail view, not
            the Course List view.
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self

        Deprecated fields:

        * blocks_url: Used to fetch the course blocks
        * course_id: Course key (use 'id' instead)

    **Parameters:**

        username (optional):
            The username of the specified user for whom the course data
            is being accessed. The username is not only required if the API is
            requested by an Anonymous user.

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.

        Example response:

            {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                    "course_image": {
                        "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                        "name": "Course Image"
                    }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "overview: "<p>A verbose description of the course.</p>"
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp",
                "pacing": "instructor"
            }
    """

    serializer_class = Custom_CourseDetailSerializer

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        requested_params = self.request.query_params.copy()
        course_title = self.kwargs["course_title"]
        # course_det = course_title.replace("-"," ")
        # log.info(u" course title %s", course_title)
        course_key = course_extrainfo.objects.get(course_seo_url=course_title)
        # course_key = CourseOverview.objects.get(display_name__icontains=course_det)
        # log.info(u" course key %s", course_key.__dict__)
        # log.info(u" course id %s", course_key)
        # for courseid in course_key:
        requested_params.update({"course_key": course_key.course_id})
        form = CourseDetailGetForm(
            requested_params, initial={"requesting_user": self.request.user}
        )
        if not form.is_valid():
            raise ValidationError(form.errors)

        return custom_course_detail(
            self.request,
            form.cleaned_data["username"],
            form.cleaned_data["course_key"],
        )


@view_auth_classes(is_authenticated=False)
class wp_home_ongoing_courses(DeveloperErrorViewMixin, RetrieveAPIView):
    def get(self, request, **kwargs):

        index_courses = course_extrainfo.objects.filter(course_type=1).values()
        index_cid = []
        for index_course in index_courses:
            index_course_id = CourseKey.from_string(index_course["course_id"])
            index_cid.append(index_course_id)

        today_date_time = datetime.datetime.now(UTC)
        courses = (
            CourseOverview.objects.all()
            .filter(
                pk__in=index_cid,
                start__lte=today_date_time,
                end__gte=today_date_time,
                catalog_visibility="both",
            )
            .order_by("start")[::-1]
        )
        ongoing_course_list = []
        for course in courses:
            ongoing_course_dict = {}
            course_id = str(course.id)
            course_extra_info = course_extrainfo.objects.get(course_id=course.id)
            # log.info(u"query %s",course.id)
            assoc_name = Organization.objects.get(
                short_name=course.display_org_with_default
            )
            data = assoc_name.name
            info = (data[:8] + "..") if len(data) > 10 else data
            course_name = (
                (course.display_name[:40] + "..")
                if len(course.display_name) > 50
                else course.display_name
            )
            ongoing_course_dict["course_title"] = course_name
            ongoing_course_dict["org"] = info
            ongoing_course_dict["media"] = course.course_image_url
            if course_extra_info:
                ongoing_course_dict["wp_url"] = (
                    "https://docmode.org/" + course_extra_info.course_seo_url
                )
                ongoing_course_dict["course_type"] = "Course"
            ongoing_course_dict["start"] = course.start.strftime("%b %d, %Y ")
            ongoing_course_dict[
                "microsite_visible"
            ] = course_extra_info.microsite_visibile_only
            ongoing_course_list.append(ongoing_course_dict)

        home_ongoing_course_list = []
        home_ongoing_course_dict = {}
        home_ongoing_course_dict["name"] = "On going Courses"
        home_ongoing_course_dict["value"] = ongoing_course_list
        home_ongoing_course_list.append(home_ongoing_course_dict)
        return JsonResponse(home_ongoing_course_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class wp_home_upcoming_lectures(DeveloperErrorViewMixin, RetrieveAPIView):
    def get(self, request, **kwargs):

        index_courses = course_extrainfo.objects.filter(course_type=2).values()
        index_cid = []
        for index_course in index_courses:
            index_course_id = CourseKey.from_string(index_course["course_id"])
            index_cid.append(index_course_id)

        today_date_time = datetime.date.today()
        courses = CourseOverview.objects.all().filter(
            pk__in=index_cid, start__gte=today_date_time, catalog_visibility="both"
        )
        ongoing_course_list = []
        for course in courses:
            ongoing_course_dict = {}
            course_id = str(course.id)
            course_extra_info = course_extrainfo.objects.get(course_id=course.id)
            # log.info(u"query %s",course.id)
            assoc_name = Organization.objects.get(
                short_name=course.display_org_with_default
            )
            data = assoc_name.name
            info = (data[:8] + "..") if len(data) > 10 else data
            course_name = (
                (course.display_name[:40] + "..")
                if len(course.display_name) > 50
                else course.display_name
            )
            ongoing_course_dict["course_title"] = course_name
            ongoing_course_dict["org"] = info
            ongoing_course_dict["media"] = course.course_image_url
            if course_extra_info:
                ongoing_course_dict["wp_url"] = (
                    "https://docmode.org/" + course_extra_info.course_seo_url
                )
                ongoing_course_dict["course_type"] = "Course"
            ongoing_course_dict["start"] = course.start.strftime("%b %d, %Y ")
            ongoing_course_list.append(ongoing_course_dict)

        home_ongoing_course_list = []
        home_ongoing_course_dict = {}
        home_ongoing_course_dict["name"] = "On going Lectures"
        home_ongoing_course_dict["value"] = ongoing_course_list
        home_ongoing_course_list.append(home_ongoing_course_dict)
        return JsonResponse(home_ongoing_course_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class doctor_lists(DeveloperErrorViewMixin, RetrieveAPIView):
    def get(self, request, **kwargs):

        pagecount = request.GET.get("pagecount")
        usertype_drs = extrafields.objects.all().filter(user_type="dr")[:500]
        user_profile_basic_list = []
        for usertype_dr in usertype_drs:
            user = User.objects.get(id=usertype_dr.user_id)
            profile = getuserfullprofile(usertype_dr.user_id)
            specz_name = specializationName(usertype_dr.specialization_id)
            profile_image = get_profile_image_urls_for_user(user, request=None)
            prof_img = profile_image["large"].split("?v")
            user_profile_data_dict = {}
            user_profile_data_dict["user_id"] = user.id
            user_profile_data_dict["user_full_name"] = profile.name
            user_profile_data_dict["profile_image"] = prof_img[0]
            user_profile_data_dict["user_full_name"] = profile.name
            user_profile_data_dict["user_specialization"] = specz_name
            user_profile_basic_list.append(user_profile_data_dict)

            doctor_api_dict = {}
            doctor_api_dict["ServiceName"] = specz_name
            doctor_api_dict["DoctorName"] = profile.name
            doctor_api_dict["Education"] = usertype_dr.education
            doctor_api_dict["Qualification"] = ""
            doctor_api_dict["Department"] = specz_name
            doctor_api_dict["Specialization"] = specz_name
            doctor_api_dict["Publications"] = ("",)
            doctor_api_dict["ShortProfile"] = profile.bio
            doctor_api_dict["Facebook"] = ""
            doctor_api_dict["Twitter"] = ""
            doctor_api_dict["Linkedin"] = ""
            doctor_api_dict["MOHID"] = usertype_dr.reg_num
            doctor_api_dict["Gender"] = ""
            doctor_api_dict["BankName"] = ""
            doctor_api_dict["BankAccountNumber"] = ""
            doctor_api_dict["BankIbnNumber"] = ""
            doctor_api_dict["BankCurrency"] = ""
            doctor_api_dict["Pobox"] = usertype_dr.rpincode
            doctor_api_dict["Address1"] = usertype_dr.address
            doctor_api_dict["GeneralTelephone"] = ""
            doctor_api_dict["GeneralEmailAddress"] = user.email
            doctor_api_dict["MobileNumber"] = usertype_dr.phone
            doctor_api_dict["StateName"] = usertype_dr.rstate

            # response = requests.post('https://ternn.com/DoctorAndMeApi/api/service/DataBaseMapWithDocMode/post', doctor_api_dict)
            # log.info(u'status-> %s',response.status_code)
        return JsonResponse(user_profile_basic_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class user_profile_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        requested_params = self.request.query_params.copy()
        user_url = self.kwargs["user_seo_url"]
        userid = extrafields.objects.get(user_seo_url=user_url)
        user = User.objects.get(id=userid.user_id)
        profile = getuserfullprofile(user.id)
        specz_name = specializationName(userid.specialization_id)
        profile_image = get_profile_image_urls_for_user(user, request=None)
        prof_img = profile_image["large"].split("?v")

        user_profile_basic_list = []
        user_profile_data_dict = {}
        user_profile_data_dict["profile_image"] = prof_img[0]
        user_profile_data_dict["user_full_name"] = profile.name
        user_profile_data_dict["user_specialization"] = specz_name
        user_profile_data_dict["bio"] = profile.bio
        user_profile_data_dict["education"] = userid.education
        user_profile_data_dict["philosophy"] = userid.medical_philosophy
        user_profile_basic_list.append(user_profile_data_dict)

        user_enrolled_courses = CourseEnrollment.objects.filter(
            user_id=user.id, is_active=1
        )
        cid = []
        for courseid in user_enrolled_courses:
            course_id = courseid.course_id
            # log.info(u"enrolled courseid %s", course_id)
            cid.append(course_id)

        courses = (
            CourseOverview.objects.all().filter(pk__in=cid).order_by("start")[::-1]
        )
        user_enroll_list = []
        assoc_course_list = []
        for course in courses:
            # log.info(u"courses %s", course)
            assoc_course_dict = {}
            course_id = str(course.id)
            course_extra_info = course_extrainfo.objects.get(course_id=course.id)
            # log.info(u"query %s",course.id)
            association = Organization.objects.get(
                short_name=course.display_org_with_default
            )
            data = association.name
            info = (data[:8] + "..") if len(data) > 10 else data
            course_name = (
                (course.display_name[:40] + "..")
                if len(course.display_name) > 50
                else course.display_name
            )
            assoc_course_dict["course_title"] = course_name
            assoc_course_dict["org"] = info
            assoc_course_dict["media"] = course.course_image_url
            if course_extra_info:
                assoc_course_dict["wp_url"] = (
                    "https://www.docmode.org/" + course_extra_info.course_seo_url
                )

                if course_extra_info.course_type == "1":
                    assoc_course_dict["course_type"] = "Course"
                elif course_extra_info.course_type == "2":
                    assoc_course_dict["course_type"] = "Lecture"
                else:
                    assoc_course_dict["course_type"] = "Case Study"
            assoc_course_dict["start"] = course.start.strftime("%b %d, %Y ")
            assoc_course_list.append(assoc_course_dict)
        user_enroll_list.append(assoc_course_list)

        user_edu_data_list = []
        education_data = education.objects.all().filter(user=user.id)
        for edu in education_data:
            user_edu_data_dict = {}
            user_edu_data_dict["year"] = edu.year
            user_edu_data_dict["institution_name"] = edu.institution_name
            user_edu_data_dict["description"] = edu.description
            user_edu_data_list.append(user_edu_data_dict)

        user_award_data_list = []
        award_data = awards.objects.all().filter(user=user.id)
        for award in award_data:
            user_award_data_dict = {}
            user_award_data_dict["year"] = award.year
            user_award_data_dict["title"] = award.title
            user_award_data_list.append(user_award_data_dict)

        user_research_data_list = []
        research_data = research_papers.objects.all().filter(user=user.id)
        for research in research_data:
            user_research_data_dict = {}
            user_research_data_dict["title"] = research.title
            user_research_data_dict["description"] = research.description
            user_research_data_dict["pdf_path"] = research.pdf_path
            user_research_data_list.append(user_research_data_dict)

        user_featured_data_list = []
        featured_data = media_featured.objects.all().filter(user=user.id)
        for featured in featured_data:
            user_featured_data_dict = {}
            user_featured_data_dict["title"] = featured.title
            user_featured_data_dict["media_name"] = featured.media_name
            user_featured_data_dict["media_link"] = featured.media_link
            user_featured_data_dict["image"] = featured.img
            user_featured_data_list.append(user_featured_data_dict)

        user_clinic_address_data_list = []
        clinic_hospital_data = clinic_hospital_address.objects.all().filter(
            user=user.id
        )
        for clinic in clinic_hospital_data:
            user_clinic_address_data_dict = {}
            user_clinic_address_data_dict["name"] = clinic.clinic_hospital_name
            user_clinic_address_data_dict["timings"] = clinic.timings
            user_clinic_address_data_dict["address_line1"] = clinic.address_line1
            user_clinic_address_data_dict["address_line2"] = clinic.address_line2
            user_clinic_address_data_dict["address_line3"] = clinic.address_line3
            user_clinic_address_data_dict["phone"] = clinic.phone_number
            user_clinic_address_data_list.append(user_clinic_address_data_dict)

        userprofile = UserProfile.objects.get(user_id=user.id)
        userprofile_extrainfo = extrafields.objects.get(user_id=user.id)

        user_certificate_list = []
        course_certificates = certificate_api.get_certificates_for_user(user.username)
        for certificate in course_certificates:
            certificate_url = certificate["download_url"]
            course = certificate["course_key"]
            courseid = CourseOverview.objects.get(id=course)
            cert_org = Organization.objects.get(
                short_name=courseid.display_org_with_default
            )
            course_name = (
                (courseid.display_name_with_default[:55])
                if len(courseid.display_name_with_default) > 40
                else courseid.display_name_with_default
            )
            dateStr = certificate["created"].strftime("%b %d, %Y ")
            ctype_numb = course_ctype_number(courseid.id)

            user_certificate_dict = {}
            user_certificate_dict["download_url"] = certificate_url
            user_certificate_dict["association_logo"] = cert_org.logo
            user_certificate_dict["name"] = course_name
            if ctype_numb == "1":
                user_certificate_dict["completed_title"] = "Course Completed"
                user_certificate_dict[
                    "medallion"
                ] = "https://s3-ap-southeast-1.amazonaws.com/docmode.co/website-images/Medal-Courses.png"
            elif ctype_numb == "2":
                user_certificate_dict["completed_title"] = "Lecture Completed"
                user_certificate_dict[
                    "medallion"
                ] = "https://s3-ap-southeast-1.amazonaws.com/docmode.co/website-images/Medal-Lectures.png"
            user_certificate_dict["date"] = dateStr
            user_certificate_list.append(user_certificate_dict)

        user_profile_data = []

        user_profile_basic_dict = {}
        user_profile_basic_dict["name"] = "Profile"
        user_profile_basic_dict["value"] = user_profile_basic_list
        user_profile_data.append(user_profile_basic_dict)

        user_certificate_dict = {}
        user_certificate_dict["name"] = "Certification for Continuing Medical Education"
        user_certificate_dict["value"] = user_certificate_list
        user_profile_data.append(user_certificate_dict)

        user_enroll_course_dict = {}
        user_enroll_course_dict["name"] = "Courses Enrolled"
        user_enroll_course_dict["value"] = user_enroll_list
        user_profile_data.append(user_enroll_course_dict)

        user_edu_data_dict = {}
        user_edu_data_dict["name"] = "Education"
        user_edu_data_dict["value"] = user_edu_data_list
        user_profile_data.append(user_edu_data_dict)

        user_award_data_dict = {}
        user_award_data_dict["name"] = "Awards"
        user_award_data_dict["value"] = user_award_data_list
        user_profile_data.append(user_award_data_dict)

        user_research_data_dict = {}
        user_research_data_dict["name"] = "Research"
        user_research_data_dict["value"] = user_research_data_list
        user_profile_data.append(user_research_data_dict)

        user_featured_data_dict = {}
        user_featured_data_dict["name"] = "Featured"
        user_featured_data_dict["value"] = user_featured_data_list
        user_profile_data.append(user_featured_data_dict)

        user_clinic_address_data_dict = {}
        user_clinic_address_data_dict["name"] = "Clinic Adress"
        user_clinic_address_data_dict["value"] = user_clinic_address_data_list
        user_profile_data.append(user_clinic_address_data_dict)

        return JsonResponse(user_profile_data, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class doctor_and_me_user_profile_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        requested_params = self.request.query_params.copy()
        user_id = self.kwargs["user_id"]
        userid = extrafields.objects.get(user_id=user_id)
        user = User.objects.get(id=userid.user_id)
        profile = getuserfullprofile(user.id)
        specz_name = specializationName(userid.specialization_id)
        profile_image = get_profile_image_urls_for_user(user, request=None)
        prof_img = profile_image["large"].split("?v")

        user_profile_basic_list = []
        user_profile_data_dict = {}
        user_profile_data_dict["profile_image"] = prof_img[0]
        user_profile_data_dict["user_full_name"] = profile.name
        user_profile_data_dict["user_specialization"] = specz_name
        user_profile_data_dict["bio"] = profile.bio
        user_profile_data_dict["education"] = userid.education
        user_profile_data_dict["philosophy"] = userid.medical_philosophy
        user_profile_basic_list.append(user_profile_data_dict)

        user_edu_data_list = []
        education_data = education.objects.all().filter(user=user.id)
        for edu in education_data:
            user_edu_data_dict = {}
            user_edu_data_dict["year"] = edu.year
            user_edu_data_dict["institution_name"] = edu.institution_name
            user_edu_data_dict["description"] = edu.description
            user_edu_data_list.append(user_edu_data_dict)

        user_award_data_list = []
        award_data = awards.objects.all().filter(user=user.id)
        for award in award_data:
            user_award_data_dict = {}
            user_award_data_dict["year"] = award.year
            user_award_data_dict["title"] = award.title
            user_award_data_list.append(user_award_data_dict)

        user_clinic_address_data_list = []
        clinic_hospital_data = clinic_hospital_address.objects.all().filter(
            user=user.id
        )
        for clinic in clinic_hospital_data:
            user_clinic_address_data_dict = {}
            user_clinic_address_data_dict["name"] = clinic.clinic_hospital_name
            user_clinic_address_data_dict["timings"] = clinic.timings
            user_clinic_address_data_dict["address_line1"] = clinic.address_line1
            user_clinic_address_data_dict["address_line2"] = clinic.address_line2
            user_clinic_address_data_dict["address_line3"] = clinic.address_line3
            user_clinic_address_data_dict["phone"] = clinic.phone_number
            user_clinic_address_data_list.append(user_clinic_address_data_dict)

        userprofile = UserProfile.objects.get(user_id=user.id)
        userprofile_extrainfo = extrafields.objects.get(user_id=user.id)

        user_certificate_list = []
        course_certificates = certificate_api.get_certificates_for_user(user.username)
        for certificate in course_certificates:
            certificate_url = certificate["download_url"]
            course = certificate["course_key"]
            courseid = CourseOverview.objects.get(id=course)
            cert_org = Organization.objects.get(
                short_name=courseid.display_org_with_default
            )
            course_name = (
                (courseid.display_name_with_default[:55])
                if len(courseid.display_name_with_default) > 40
                else courseid.display_name_with_default
            )
            dateStr = certificate["created"].strftime("%b %d, %Y ")
            ctype_numb = course_ctype_number(courseid.id)

            user_certificate_dict = {}
            user_certificate_dict["download_url"] = certificate_url
            user_certificate_dict["association_logo"] = cert_org.logo
            user_certificate_dict["name"] = course_name
            if ctype_numb == "1":
                user_certificate_dict["completed_title"] = "Course Completed"
                user_certificate_dict[
                    "medallion"
                ] = "https://s3-ap-southeast-1.amazonaws.com/docmode.co/website-images/Medal-Courses.png"
            elif ctype_numb == "2":
                user_certificate_dict["completed_title"] = "Lecture Completed"
                user_certificate_dict[
                    "medallion"
                ] = "https://s3-ap-southeast-1.amazonaws.com/docmode.co/website-images/Medal-Lectures.png"
            user_certificate_dict["date"] = dateStr
            user_certificate_list.append(user_certificate_dict)

        user_profile_data = []

        user_profile_basic_dict = {}
        user_profile_basic_dict["name"] = "Profile"
        user_profile_basic_dict["value"] = user_profile_basic_list
        user_profile_data.append(user_profile_basic_dict)

        user_certificate_dict = {}
        user_certificate_dict["name"] = "Certification for Continuing Medical Education"
        user_certificate_dict["value"] = user_certificate_list
        user_profile_data.append(user_certificate_dict)

        user_edu_data_dict = {}
        user_edu_data_dict["name"] = "Education"
        user_edu_data_dict["value"] = user_edu_data_list
        user_profile_data.append(user_edu_data_dict)

        user_award_data_dict = {}
        user_award_data_dict["name"] = "Awards"
        user_award_data_dict["value"] = user_award_data_list
        user_profile_data.append(user_award_data_dict)

        user_clinic_address_data_dict = {}
        user_clinic_address_data_dict["name"] = "Clinic Adress"
        user_clinic_address_data_dict["value"] = user_clinic_address_data_list
        user_profile_data.append(user_clinic_address_data_dict)

        return JsonResponse(user_profile_data, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class ad_manager_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        from lms.djangoapps.add_manager.views import (
            sponsored_user,
            get_association_ad_data,
            user_ad_view_counter,
        )
        from lms.djangoapps.reg_form.views import get_authuser
        from lms.djangoapps.add_manager.models import user_view_counter
        from django.db.models import F

        if "course_id" and "user" in request.GET:
            user_name = request.GET.get("user")
            try:
                user = User.objects.get(username=user_name)
                # user = get_authuser(user_query.id)

            except:
                result = {}
                result["Message"] = "Invalid User"
                return JsonResponse(result, status=404)
            courseid = request.GET.get("course_id").replace(" ", "+")
            course_id = CourseKey.from_string(courseid)
            user_course = sponsored_user(user, course_id)
            user_ad_view = user_ad_view_counter(user.id, course_id)
            log.info(u"user_course-> %s", user_course)
            log.info(u"user_ad_view-> %s", user_ad_view)
            if user_course != "n/a":
                result = {}
                result["Data"] = {"video_url": user_course}
                result["sponsored_user"] = "true"
                if user_ad_view > 0:
                    result["first_time"] = "false"
                    update_counter = user_view_counter.objects.filter(
                        course_id=course_id, user=user.id
                    ).update(mcounter=F("mcounter") + 1)
                else:
                    result["first_time"] = "true"
                    countr = user_view_counter(
                        user_id=user.id, course_id=course_id, mcounter=1
                    )
                    countr.save()
            else:
                result = {}
                result["sponsored_user"] = "false"
            return JsonResponse(result, status=200, safe=False)

        elif "course_id" and "ad_user" in request.GET:
            courseid = request.GET.get("course_id").replace(" ", "+")
            course_id = CourseKey.from_string(courseid)
            user_name = request.GET.get("ad_user")
            try:
                user = User.objects.get(username=user_name)
            except:
                result = {}
                result["Message"] = "Invalid User"
                return JsonResponse(result, status=404)

            assoc_ad = get_association_ad_data(course_id)
            user_ad_view = user_ad_view_counter(user.id, course_id)
            if assoc_ad != "n/a":
                result = {}
                result["sponsored_lecture"] = "true"
                result["Data"] = {"video_url": assoc_ad}
                if user_ad_view > 0:
                    result["first_time"] = "false"
                    update_counter = user_view_counter.objects.filter(
                        course_id=course_id, user=user.id
                    ).update(mcounter=F("mcounter") + 1)
                else:
                    result["first_time"] = "true"
                    countr = user_view_counter(
                        user_id=user.id, course_id=course_id, mcounter=1
                    )
                    countr.save()
            else:
                result = {}
                result["sponsored_lecture"] = "false"
            return JsonResponse(result, status=200, safe=False)
        else:
            message = "course_id paramater missing"
            result = {}
            result["Data"] = {}
            result["Status"] = "false"
            result["Message"] = message
            return JsonResponse(result, status=404)


@view_auth_classes(is_authenticated=False)
class wp_courses(DeveloperErrorViewMixin, RetrieveAPIView):
    def get(self, request, **kwargs):

        index_courses = course_extrainfo.objects.filter(course_type=1).values()
        index_cid = []
        for index_course in index_courses:
            index_course_id = CourseKey.from_string(index_course["course_id"])
            index_cid.append(index_course_id)

        today_date_time = datetime.datetime.now(UTC)
        courses = (
            CourseOverview.objects.all()
            .filter(pk__in=index_cid, catalog_visibility="both")
            .order_by("start")[::-1]
        )
        ongoing_course_list = []
        for course in courses:
            ongoing_course_dict = {}
            course_id = str(course.id)
            course_extra_info = course_extrainfo.objects.get(course_id=course.id)
            # log.info(u"query %s",course.id)
            assoc_name = Organization.objects.get(
                short_name=course.display_org_with_default
            )
            data = assoc_name.name
            info = (data[:8] + "..") if len(data) > 10 else data
            course_name = (
                (course.display_name[:40] + "..")
                if len(course.display_name) > 50
                else course.display_name
            )
            ongoing_course_dict["course_title"] = course_name
            ongoing_course_dict["org"] = info
            ongoing_course_dict["media"] = course.course_image_url
            if course_extra_info:
                ongoing_course_dict["wp_url"] = (
                    "https://docmode.org/" + course_extra_info.course_seo_url
                )
                ongoing_course_dict["course_type"] = "Course"
            ongoing_course_dict["start"] = course.start.strftime("%b %d, %Y ")
            ongoing_course_list.append(ongoing_course_dict)

        home_ongoing_course_list = []
        home_ongoing_course_dict = {}
        home_ongoing_course_dict["name"] = "Courses"
        home_ongoing_course_dict["value"] = ongoing_course_list
        home_ongoing_course_list.append(home_ongoing_course_dict)
        return JsonResponse(home_ongoing_course_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class wp_lectures(DeveloperErrorViewMixin, RetrieveAPIView):
    def get(self, request, **kwargs):

        index_courses = course_extrainfo.objects.filter(course_type=2).values()
        index_cid = []
        for index_course in index_courses:
            index_course_id = CourseKey.from_string(index_course["course_id"])
            index_cid.append(index_course_id)

        today_date_time = datetime.datetime.now(UTC)
        courses = (
            CourseOverview.objects.all()
            .filter(pk__in=index_cid, catalog_visibility="both")
            .order_by("start")[::-1]
        )
        ongoing_course_list = []
        for course in courses:
            ongoing_course_dict = {}
            course_id = str(course.id)
            course_extra_info = course_extrainfo.objects.get(course_id=course.id)
            # log.info(u"query %s",course.id)
            assoc_name = Organization.objects.get(
                short_name=course.display_org_with_default
            )
            data = assoc_name.name
            info = (data[:8] + "..") if len(data) > 10 else data
            course_name = (
                (course.display_name[:40] + "..")
                if len(course.display_name) > 50
                else course.display_name
            )
            ongoing_course_dict["course_title"] = course_name
            ongoing_course_dict["org"] = info
            ongoing_course_dict["media"] = course.course_image_url
            if course_extra_info:
                ongoing_course_dict["wp_url"] = (
                    "https://docmode.org/" + course_extra_info.course_seo_url
                )
                ongoing_course_dict["course_type"] = "Course"
            ongoing_course_dict["start"] = course.start.strftime("%b %d, %Y ")
            ongoing_course_list.append(ongoing_course_dict)

        home_ongoing_course_list = []
        home_ongoing_course_dict = {}
        home_ongoing_course_dict["name"] = "Lectures"
        home_ongoing_course_dict["value"] = ongoing_course_list
        home_ongoing_course_list.append(home_ongoing_course_dict)
        return JsonResponse(home_ongoing_course_list, status=200, safe=False)


def logout_redirect(request, redirecturl):
    main_url = "https://cims.docmode.org/" + redirecturl
    log.info(u"newredirect-> %s", main_url)
    return HttpResponseRedirect(main_url)


@receiver(COURSE_GRADE_NOW_PASSED)
def send_completion_mail(sender, user=None, course_id=None, **kwargs):
    from bulk_email.models import CourseEmailTemplate, CourseEmail

    log.info("->-> CC == %s ++ %s ++ %s", user, course_id)

    course_email = CourseEmail.objects.get(id=49)
    log.info(u"course_email %s", course_email)
    connection = get_connection()
    connection.open()
    cid1 = str(course_email.course_id)
    log.info(u"cid-> %s", cid1)
    if "FGS0025" in cid1:

        userprofile = getuserfullprofile(user.id)
        email = user.email
        subject = "Congratulations on completing DASIL Accredited Digital Trichology & Trichosurgery Workshop 2020"
        message = "Congratulations" + user.username + "you are enrolled in the course"

        from_addr = "Docmode <info@docmode.org>"
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


# @receiver(ENROLL_STATUS_CHANGE)
def send_welcome_email(sender, event=None, user=None, course_id=None, **kwargs):
    from bulk_email.models import CourseEmailTemplate, CourseEmail

    if event == EnrollStatusChange.enroll:
        course_email = CourseEmail.objects.get(id=4)
        cid1 = str(course_id)
        connection = get_connection()
        connection.open()
        if "CIMS002" in cid1:
            log.info(u"cid1-> %s", cid1)
            email = user.email
            subject = "Congratulations on Enrolling to DASIL Accredited Digital Trichology & Trichosurgery Workshop 2020"
            message = (
                "Congratulations" + user.username + "you are enrolled in the course"
            )
            userprofile = getuserfullprofile(user.id)
            from_addr = "Docmode <info@docmode.org>"
            course = get_course(course_id)
            global_email_context = _get_course_email_context(course)

            email_context = {"name": "", "email": ""}
            email_context.update(global_email_context)
            email_context["email"] = email
            email_context["name"] = userprofile.name
            email_context["user_id"] = user.id
            email_context["course_id"] = course_id

            course_email = CourseEmail.objects.get(id=4)
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


def str2bool(s):
    s = str(s)
    return s.lower() in ("yes", "true", "t", "1")


@view_auth_classes(is_authenticated=False)
class user_registration_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        generated_password = generate_password()

        if request.method == "GET":

            username = request.GET.get("username", "")
            email = request.GET.get("emailid", "")
            password = request.GET.get("password", generated_password)
            full_name = request.GET.get("name", "")
            phone = request.GET.get("phone", "")
            user_type = request.GET.get("user_type", "")
            pincode = request.GET.get("pincode", "")
            country = request.GET.get("country", "")
            state = request.GET.get("state", "")
            city = request.GET.get("city", "")
            is_active = str2bool(request.GET.get("is_active", True))

            form = AccountCreationForm(
                data={
                    "username": username,
                    "email": email,
                    "password": password,
                    "name": full_name,
                },
                tos_required=False,
            )
            restricted = settings.FEATURES.get("RESTRICT_AUTOMATIC_AUTH", True)
            try:
                user, profile, reg = do_create_account(form)
                log.info(u"user--> %s", user)
            except (AccountValidationError, ValidationError):
                # if restricted:
                #     return HttpResponseForbidden(_('Account modification not allowed.'))
                # Attempt to retrieve the existing user.
                #     user = User.objects.get(username=username)
                #     user.email = email
                #     user.set_password(password)
                #     user.is_active = is_active
                #     user.save()
                #     profile = UserProfile.objects.get(user=user)
                #     reg = Registration.objects.get(user=user)
                # except PermissionDenied:
                api_params = []
                for key, value in request.GET.iteritems():
                    userdata = {}
                    userdata[key] = value
                    api_params.append(userdata)
                registration_log = third_party_user_registration_log(
                    email=email,
                    status="Account creation not allowed either the user is already registered or email-id not valid",
                    data=api_params,
                )
                registration_log.save()
                return HttpResponseForbidden(
                    "Account creation not allowed either the user is already registered or email-id not valid."
                )

            if is_active:
                reg.activate()
                reg.save()

            # ensure parental consent threshold is met
            year = datetime.date.today().year
            age_limit = settings.PARENTAL_CONSENT_AGE_LIMIT
            profile.year_of_birth = (year - age_limit) - 1
            profile.save()
            user_extrainfo = extrafields(
                phone=phone,
                rcountry=country,
                rstate=state,
                rcity=city,
                rpincode=pincode,
                user_type=user_type,
                user=user,
            )
            user_extrainfo.save()
            new_user = authenticate_new_user(request, user.username, password)
            django_login(request, new_user)
            request.session.set_expiry(0)

            create_comments_service_user(user)

            create_or_set_user_attribute_created_on_site(user, request.site)
            course_id = "course-v1:PCOS-Society+PCS004+2020_Dec_PCS004"
            course_key = None
            if course_id:
                course_key = CourseKey.from_string(course_id)
                course_mode = "audit"
                CourseEnrollment.enroll(user, course_key, mode=course_mode)

            api_params = []
            for key, value in request.GET.iteritems():
                userdata = {}
                userdata[key] = value
                api_params.append(userdata)
            registration_log = third_party_user_registration_log(
                email=email, status="succesful", data=api_params
            )
            registration_log.save()
            home_ongoing_course_list = []
            home_ongoing_course_dict = {}
            home_ongoing_course_dict["response"] = "Success"
            return HttpResponse("Registration successfully")
        else:
            home_ongoing_course_list = []
            home_ongoing_course_dict = {}
            home_ongoing_course_dict["response"] = "Failed"
            api_params = []
            for key, value in request.GET.iteritems():
                userdata = {}
                userdata[key] = value
                api_params.append(userdata)
            registration_log = third_party_user_registration_log(
                email=email, status="failed", data=api_params
            )
            registration_log.save()
            return HttpResponse("Registration failed")


@view_auth_classes(is_authenticated=False)
class user_basic_data(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        requested_params = self.request.query_params.copy()
        emailid = self.kwargs["emailid"]
        user = User.objects.get(email=emailid)
        userid = extrafields.objects.get(user_id=user.id)
        profile = getuserfullprofile(user.id)
        specz_name = specializationName(userid.specialization_id)
        signupdate = user.date_joined.astimezone(timezone("Asia/Kolkata"))

        user_basic_list = []
        user_data_dict = {}
        user_data_dict["user_id"] = user.id
        user_data_dict["full_name"] = profile.name
        user_data_dict["is_staff"] = user.is_staff
        user_data_dict["user_type"] = userid.user_type
        user_data_dict["specialization"] = specz_name
        user_data_dict["mobile"] = userid.phone
        user_data_dict["registration_number"] = userid.reg_num
        user_data_dict["country"] = userid.rcountry
        user_data_dict["state"] = userid.rstate
        user_data_dict["city"] = userid.rcity
        user_data_dict["pincode"] = userid.rpincode
        user_data_dict["verification_status"] = user.is_active
        if user.is_active == 1:
            user_data_dict["is_verified"] = 1
        else:
            try:
                inactive_user_login_count = LoginFailures.objects.get(user_id=user.id)
                remaining_passes = 5 - inactive_user_login_count.failure_count
                user_data_dict["remaining_passes"] = remaining_passes
            except:
                user_data_dict["remaining_passes"] = 5
            user_data_dict["is_verified"] = 0
        user_data_dict["signup_date"] = signupdate.strftime("%Y-%m-%d %H:%M:%S")

        user_basic_list.append(user_data_dict)

        user_basic_data = []
        user_data_dict = {}
        user_data_dict["name"] = "Basic data"
        user_data_dict["value"] = user_basic_list
        user_basic_data.append(user_data_dict)

        return JsonResponse(user_basic_data, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class user_data_username(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        requested_params = self.request.query_params.copy()
        username = self.kwargs["username"]
        user = User.objects.get(username=username)
        userid = extrafields.objects.get(user_id=user.id)
        profile = getuserfullprofile(user.id)
        specz_name = specializationName(userid.specialization_id)
        signupdate = user.date_joined.astimezone(timezone("Asia/Kolkata"))

        user_basic_list = []
        user_data_dict = {}
        user_data_dict["user_id"] = user.id
        user_data_dict["full_name"] = profile.name
        user_data_dict["is_staff"] = user.is_staff
        user_data_dict["user_type"] = userid.user_type
        user_data_dict["specialization"] = specz_name
        user_data_dict["mobile"] = userid.phone
        user_data_dict["registration_number"] = userid.reg_num
        user_data_dict["country"] = userid.rcountry
        user_data_dict["state"] = userid.rstate
        user_data_dict["city"] = userid.rcity
        user_data_dict["pincode"] = userid.rpincode
        user_data_dict["verification_status"] = user.is_active
        if user.is_active == 1:
            user_data_dict["is_verified"] = 1
        else:
            try:
                inactive_user_login_count = LoginFailures.objects.get(user_id=user.id)
                remaining_passes = 5 - inactive_user_login_count.failure_count
                user_data_dict["remaining_passes"] = remaining_passes
            except:
                user_data_dict["remaining_passes"] = 5
            user_data_dict["is_verified"] = 0
        user_data_dict["signup_date"] = signupdate.strftime("%Y-%m-%d %H:%M:%S")

        user_basic_list.append(user_data_dict)

        user_basic_data = []
        user_data_dict = {}
        user_data_dict["name"] = "Basic data"
        user_data_dict["value"] = user_basic_list
        user_basic_data.append(user_data_dict)

        return JsonResponse(user_basic_data, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class user_course_enrollment_status(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        requested_params = self.request.query_params.copy()
        emailid = self.kwargs["emailid"]
        user = User.objects.get(email=emailid)
        userid = extrafields.objects.get(user_id=user.id)
        profile = getuserfullprofile(user.id)
        specz_name = specializationName(userid.specialization_id)
        signupdate = user.date_joined.astimezone(timezone("Asia/Kolkata"))

        user_basic_list = []
        user_data_dict = {}
        user_data_dict["user_id"] = user.id
        user_data_dict["full_name"] = profile.name
        user_data_dict["is_staff"] = user.is_staff
        user_data_dict["user_type"] = userid.user_type
        user_data_dict["specialization"] = specz_name
        user_data_dict["mobile"] = userid.phone
        user_data_dict["registration_number"] = userid.reg_num
        user_data_dict["country"] = userid.rcountry
        user_data_dict["state"] = userid.rstate
        user_data_dict["city"] = userid.rcity
        user_data_dict["pincode"] = userid.rpincode
        user_data_dict["verification_status"] = user.is_active
        user_data_dict["signup_date"] = signupdate.strftime("%Y-%m-%d %H:%M:%S")

        user_basic_list.append(user_data_dict)

        user_basic_data = []
        user_data_dict = {}
        user_data_dict["name"] = "Basic data"
        user_data_dict["value"] = user_basic_list
        user_basic_data.append(user_data_dict)

        return JsonResponse(user_basic_data, status=200, safe=False)


##############docvidya registration api####################
@view_auth_classes(is_authenticated=False)
class docvidya_user_registration_api(DeveloperErrorViewMixin, APIView):
    def post(self, request, **kwargs):
        generated_password = generate_password()

        if request.method == "POST":
            data = request.POST.dict()
            email = data.get("emailid", "")
            log.info(u"email1--> %s", email)
            password = "Docmode"
            full_name = data.get("name", "")
            phone = data.get("phone", "")
            user_type = data.get("user_type", "")
            pincode = data.get("pincode", "")
            country = data.get("country", "")
            state = data.get("state", "")
            city = data.get("city", "")
            is_active = True

            username = email.split("@")
            uname = username[0]
            log.info(u"uname--> %s", uname)
            try:
                email_check = User.objects.get(email=email)
                extradata = {"docvidya_user": 1}
            except ObjectDoesNotExist:
                extradata = {"docmode_user": 1}

                log.info(u"extradata--> %s", extradata)
            try:
                username_validation = User.objects.get(username=uname)
                if username_validation:
                    date = datetime.datetime.now()
                    curr_time = date.strftime("%f")
                    username = uname + "_" + curr_time
            except ObjectDoesNotExist:
                username = uname
            log.info(u"username--> %s", username)
            form = AccountCreationForm(
                data={
                    "username": username,
                    "email": email,
                    "password": password,
                    "name": full_name,
                },
                tos_required=False,
            )

            log.info(u"form--> %s", form)
            restricted = settings.FEATURES.get("RESTRICT_AUTOMATIC_AUTH", True)
            try:
                user, profile, reg = do_create_account(form)
                log.info(u"user--> %s", user)
            except (AccountValidationError, ValidationError):
                # if restricted:
                #     return HttpResponseForbidden(_('Account modification not allowed.'))
                # Attempt to retrieve the existing user.
                #     user = User.objects.get(username=username)
                #     user.email = email
                #     user.set_password(password)
                #     user.is_active = is_active
                #     user.save()
                #     profile = UserProfile.objects.get(user=user)
                #     reg = Registration.objects.get(user=user)
                # except PermissionDenied:
                registration_log = third_party_user_registration_log(
                    email=email,
                    status="Account creation not allowed either the user is already registered or email-id not valid",
                    data=request.POST.dict(),
                )
                registration_log.save()
                return HttpResponseForbidden(
                    "Account creation not allowed either the user is already registered or email-id not valid."
                )

            if is_active:
                reg.activate()
                reg.save()

            # ensure parental consent threshold is met
            year = datetime.date.today().year
            age_limit = settings.PARENTAL_CONSENT_AGE_LIMIT
            profile.year_of_birth = (year - age_limit) - 1
            profile.save()
            user_extrainfo = extrafields(
                phone=phone,
                rcountry=country,
                rstate=state,
                rcity=city,
                rpincode=pincode,
                user_type=user_type,
                user=user,
                user_extra_data=extradata,
            )
            user_extrainfo.save()
            create_comments_service_user(user)

            create_or_set_user_attribute_created_on_site(user, request.site)

            registration_log = third_party_user_registration_log(
                email=email, status="succesful", data=request.POST.dict()
            )
            registration_log.save()
            home_ongoing_course_list = []
            home_ongoing_course_dict = {}
            home_ongoing_course_dict["response"] = "Success"
            return HttpResponse("Registration successfully")
        else:
            home_ongoing_course_list = []
            home_ongoing_course_dict = {}
            home_ongoing_course_dict["response"] = "Failed"

            registration_log = third_party_user_registration_log(
                email=email, status="failed", data=request.POST.dict()
            )
            registration_log.save()
            return HttpResponse("Registration failed")


@view_auth_classes(is_authenticated=False)
class docvidya_user_profile_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        requested_params = self.request.query_params.copy()
        email = self.kwargs["email"]
        user = User.objects.get(email=email)
        userprofile = UserProfile.objects.get(user_id=user.id)
        userprofile_extrainfo = extrafields.objects.get(user_id=user.id)

        profile = getuserfullprofile(user.id)
        specz_name = specializationName(userprofile_extrainfo.specialization_id)
        profile_image = get_profile_image_urls_for_user(user, request=None)
        prof_img = profile_image["large"].split("?v")

        user_profile_basic_list = []
        user_profile_data_dict = {}
        user_profile_data_dict["profile_image"] = prof_img[0]
        user_profile_data_dict["user_full_name"] = profile.name
        user_profile_data_dict["user_specialization"] = specz_name
        user_profile_data_dict["bio"] = profile.bio
        user_profile_data_dict["education"] = userprofile_extrainfo.education
        user_profile_data_dict["philosophy"] = userprofile_extrainfo.medical_philosophy
        user_profile_basic_list.append(user_profile_data_dict)

        log.info("data--> %s", user_profile_basic_list)

        user_enrolled_courses = CourseEnrollment.objects.filter(
            user_id=user.id, is_active=1
        )
        cid = []
        for courseid in user_enrolled_courses:
            course_id = courseid.course_id
            # log.info(u"enrolled courseid %s", course_id)
            cid.append(course_id)

        courses = (
            CourseOverview.objects.all().filter(pk__in=cid).order_by("start")[::-1]
        )
        user_enroll_list = []
        assoc_course_list = []
        for course in courses:
            # log.info(u"courses %s", course)
            assoc_course_dict = {}
            course_id = str(course.id)

            assoc_course_dict["course_id"] = course_id
            assoc_course_dict["start"] = course.start.strftime("%b %d, %Y ")
            assoc_course_list.append(assoc_course_dict)
        user_enroll_list.append(assoc_course_list)

        user_certificate_list = []
        course_certificates = certificate_api.get_certificates_for_user(user.username)
        log.info("certificate--> %s", course_certificates)
        for certificate in course_certificates:
            certificate_url = certificate["download_url"]
            course = certificate["course_key"]
            courseid = CourseOverview.objects.get(id=course)

            dateStr = certificate["created"].strftime("%b %d, %Y ")

            user_certificate_dict = {}
            user_certificate_dict["download_url"] = certificate_url
            user_certificate_dict["course_id"] = str(courseid.id)

            user_certificate_dict["date"] = dateStr
            user_certificate_list.append(user_certificate_dict)

        log.info("certificate--> %s", user_certificate_list)

        user_profile_data = []

        user_certificate_dict = {}
        user_certificate_dict["name"] = "Certificates "
        user_certificate_dict["value"] = user_certificate_list
        user_profile_data.append(user_certificate_dict)

        user_enroll_course_dict = {}
        user_enroll_course_dict["name"] = "Courses Enrolled"
        user_enroll_course_dict["value"] = user_enroll_list
        user_profile_data.append(user_enroll_course_dict)

        return JsonResponse(user_profile_data, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class docvidya_popular_topics_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        enrollment_count = (
            CourseEnrollment.objects.values("course_id")
            .annotate(ccount=Count("course_id"))
            .order_by("-ccount")[:10]
        )

        popular_topic_list = []
        topicid_list = []
        for courseid in enrollment_count:
            log.info("courseid--> %s", courseid)
            try:
                topicid = course_extrainfo.objects.get(course_id=courseid["course_id"])
                log.info("topicid3--> %s", topicid.category)
                log.info("count--> %s", courseid["ccount"])
                if topicid.category not in topicid_list:
                    topicid_list.append(topicid.category)
                    log.info("topicid1--> %s", topicid_list)
                    topic_name = categories.objects.get(id=topicid.category)
                    log.info("topic_name--> %s", topic_name.topic_name)
                    popular_topic_dict = {}
                    popular_topic_dict["topic_name"] = topic_name.topic_name
                    popular_topic_dict["enrollment_count"] = courseid["ccount"]
                    popular_topic_list.append(popular_topic_dict)
                else:
                    popular_topic_dict["enrollment_count"] += courseid["ccount"]

            except:
                topic = "n/a"
        log.info("popular_topic_list %s", popular_topic_list)
        return JsonResponse(popular_topic_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class docvidya_popular_insturctor_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        enrollment_count = (
            CourseEnrollment.objects.values("course_id")
            .annotate(ccount=Count("course_id"))
            .order_by("-ccount")[:10]
        )
        instructor_list = []
        for courseid in enrollment_count:
            instructor_data = CourseAccessRole.objects.filter(
                course_id=courseid["course_id"], role="instructor"
            )
            for instructor in instructor_data:
                user = User.objects.get(id=instructor.user_id)
                user_detail = getuserfullprofile(instructor.user_id)
                user_extra_data = userdetails(instructor.user_id)
                profile_image = get_profile_image_urls_for_user(user, request=None)
                prof_img = profile_image["large"].split("?v")

                instructor_dict = {}
                instructor_dict["name"] = user_detail.name
                instructor_dict["education"] = user_extra_data.education
                instructor_dict["bio"] = user_extra_data.user_long_description
                instructor_dict["profile_image"] = (
                    "https://learn.docmode.org" + prof_img[0]
                )
                instructor_list.append(instructor_dict)

        return JsonResponse(instructor_list, status=200, safe=False)
