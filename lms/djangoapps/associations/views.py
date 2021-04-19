#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Associations views functions
"""
import csv
import json
import logging
import urllib
import MySQLdb
import requests
from collections import OrderedDict

from django.conf import settings
from django.urls import reverse
from django.utils.encoding import smart_str
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

# from common.djangoapps.organizations.import serializers

from lms.djangoapps.reg_form.models import extrafields
from lms.djangoapps.specialization.views import specializationName
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist

# from lang_pref import LANGUAGE_KEY

from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser

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

log = logging.getLogger("edx.courseware")

template_imports = {"urllib": urllib}


# Create your views here.


def index(request):
    from common.djangoapps.organizations.api import get_organizations

    # org_list = []

    org_list = get_organizations()

    sorted_assoc_list = sorted(
        org_list, key=lambda organizations: organizations["name"]
    )

    context = {"organizations": sorted_assoc_list}

    return render_to_response("associations/associations.html", context)


def list_categories(request):

    # org_list = []

    category_list = categories.objects.all().order_by("topic_name")
    context = {"categories": category_list}
    return render_to_response("associations/categories.html", context)


def list_lectures(request):
    if not request.user.is_staff:
        main_url = "https://docmode.org/lectures"
        return redirect(main_url)

    # ## HEMANT
    # enable_mktg_site = configuration_helpers.get_value(
    #    'ENABLE_MKTG_SITE',
    #    settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    # )

    # if enable_mktg_site:
    #    return redirect(marketing_link('LECTURES'), permanent=True)

    # if not settings.FEATURES.get('COURSES_ARE_BROWSABLE'):
    #    raise Http404
    # ## HEMANT

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
    user = request.user

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
            # ....sep_images = 'http://www.gettyimages.pt/gi-resources/images/Homepage/Hero/PT/PT_hero_42_153645159.jpg'
            # else:
            # ....sep_images = slider_images.image_s3_urls

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
            except ObjectDoesNotExist:

                # member_staff = OrganizationMembers.objects.get(user_id=gusr,organization_id=data.id)

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
                        .filter(Q(pk__in=scid) & Q(start__lte=datetime.date.today()))
                        .order_by("start")[::-1]
                    )
                elif course_time == "2":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(Q(pk__in=scid) & Q(start__gte=datetime.date.today()))
                        .order_by("start")[::-1]
                    )
                else:
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(pk__in=scid)
                        .order_by("start")[::-1]
                    )
            else:

                if course_time == "1":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(Q(pk__in=cid) & Q(start__lte=datetime.date.today()))
                        .order_by("start")[::-1]
                    )
                elif course_time == "2":
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(Q(pk__in=cid) & Q(start__gte=datetime.date.today()))
                        .order_by("start")[::-1]
                    )
                else:
                    sub_course_data = (
                        CourseOverview.objects.all()
                        .filter(pk__in=cid)
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
    speczname = ""
    try:
        getDetails = specializations.objects.get(id=speczId)
        speczname = getDetails.name
    except ObjectDoesNotExist:
        getDetails = None

    return speczname


def orgName(orgId):
    orgname = ""
    try:
        getDetails = Organization.objects.get(id=orgId)
        orgname = getDetails.name
    except ObjectDoesNotExist:
        getDetails = None

    return orgname


def userType(type):
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
    elif sname == "u":
        uName = "Public"
    else:
        uName = "Medical Student"
    return uName


def getuserlog(cid):
    from track.backends.django import TrackingLog

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
            extrafields.objects.values("user_type")
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
    response.write(
        u"\ufeff".encode("utf8")
    )  # BOM (optional...Excel needs it to open UTF-8 file properly)

    # log.info(u" coupondata %s", coupon_results)

    user = request.user

    if user.is_staff:
        writer.writerow([smart_str(u"Specialization"), smart_str(u"Count")])
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

    context = {"vouchers": results}  # 'title': 'Demographics Page',
    # 'locationCount': enrollLocationQset

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
    response.write(
        u"\ufeff".encode("utf8")
    )  # BOM (optional...Excel needs it to open UTF-8 file properly)

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
    response.write(
        u"\ufeff".encode("utf8")
    )  # BOM (optional...Excel needs it to open UTF-8 file properly)

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
            course_id=userId, module_type="video"
        ).count()
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
    gusr = request.user.id
    org_course = OrganizationCourse.objects.get(course_id=course_id)
    try:
        member_staff = OrganizationMembers.objects.get(
            user_id=gusr, organization_id=org_course.organization_id, is_admin="1"
        )
    except ObjectDoesNotExist:

        # member_staff = OrganizationMembers.objects.get(user_id=gusr,organization_id=data.id)

        member_staff = None

    if member_staff is None:
        grpstaff = "0"
    else:
        grpstaff = "1"

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

    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    cid = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    try:
        course = CourseOverview.objects.get(id=cid)
    except ObjectDoesNotExist:
        course = None

    try:
        enrolleduser = CourseEnrollment.objects.filter(
            course_id=cid, is_active=1
        ).count()
    except ObjectDoesNotExist:
        enrolleduser = "No data"

    try:
        viewers = StudentModule.objects.filter(
            course_id=cid, module_type="video"
        ).count()
    except ObjectDoesNotExist:
        viewers = "No data"
    data = Organization.objects.get(short_name=course.display_org_with_default)

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

    vieweduser = StudentModule.objects.filter(
        course_id=cid, module_type="video"
    ).values("student_id")
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
    }

    return render_to_response("associations/association_course_analytics.html", context)


def export_csv(request, course_id, datatype):
    from opaque_keys.edx.locations import SlashSeparatedCourseKey

    cid = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=users.csv"
    writer = csv.writer(response, csv.excel)
    response.write(
        u"\ufeff".encode("utf8")
    )  # BOM (optional...Excel needs it to open UTF-8 file properly)

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

    if user.is_staff:
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
            ]
        )
        if datatype == "enrolled":
            response["Content-Disposition"] = (
                "attachment; filename=" + str(course_number[1]) + "_enrolledusers.csv"
            )
            crows = CourseEnrollment.objects.filter(course_id=cid)
            for row in crows:
                try:
                    assoc_user = User.objects.get(id=row.user_id)
                    user_ext = userdetails(assoc_user.id)
                    writer.writerow(
                        [
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
            vrows = (
                StudentModule.objects.filter(course_id=cid, module_type="video")
                .values("student_id", "created", "state")
                .annotate(dcount=Count("student_id"))[:7000]
            )
            for vrow in vrows:

                # log.info(u'vrow-> %s',vrow['student_id'])

                assoc_user = User.objects.get(id=vrow["student_id"])
                user_ext = userdetails(assoc_user.id)
                writer.writerow(
                    [
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
            vrows = StudentModule.objects.filter(course_id=cid, module_type="video")[
                :7000
            ]
            for vrow in vrows:
                assoc_user = User.objects.get(id=vrow.student_id)
                writer.writerow(
                    [
                        smart_str(getViewerName(vrow.student_id)),
                        smart_str(getusertype(vrow.student_id).encode("ASCII")),
                        smart_str(user_ext.reg_num),
                        smart_str(getspecialization(vrow.student_id).encode("ASCII")),
                        smart_str(user_ext.rstate),
                        smart_str(user_ext.rcity),
                        smart_str(rpincode),
                        smart_str(vrow.created),
                        smart_str(vrow.state),
                        smart_str(assoc_user.is_active),
                    ]
                )

    return response


export_csv.short_description = u"Export CSV"


def autojoin_org(userid, course_id, email):
    org_id = OrganizationCourse.objects.get(course_id=course_id)

    gmember = OrganizationMembers(
        user_id=userid, organization_id=org_id.organization_id, user_email=email
    )
    gmember.save()


def assoc_join(userid, org_id, email):
    data = Organization.objects.get(short_name=org_id)
    gmember = OrganizationMembers(
        user_id=userid, organization_id=data.id, user_email=email
    )
    gmember.save()


def check_domain_in_usermail(sponsoring_companyname="lupin"):
    try:
        sname = SponsoringCompany.objects.filter(name=sponsoring_companyname)
        found = 1
    except ObjectDoesNotExist:
        found = 0
    return found


def search_list(request):
    if request.is_ajax():
        if request.method == "GET":
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


# association api's start


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
                info = data[:8] + ".." if len(data) > 10 else data
                course_name = (
                    course.display_name[:40] + ".."
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


class wp_partner_admin_api(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        requested_params = self.request.query_params.copy()
        org = self.kwargs["association_about"]
        assoc = get_assoc(org)
        wpusername = self.kwargs["emailid"]
        user_details = get_user(wpusername)
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
        user, get_permission_for_course_about(), course_key
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
    except ObjectDoesNotExist:

        # log.info(u'coursed-> %s',course_disclaimer_list)

        ad_disclaimer = "n/a"

    assoc_course_list = []
    for course in courses:
        assoc_course_dict = {}
        course_id = str(course.id)
        course_extra_info = course_extrainfo.objects.get(course_id=course.id)
        data = association.name
        info = data[:8] + ".." if len(data) > 10 else data
        course_name = (
            course.display_name[:40] + ".."
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
            self.request, form.cleaned_data["username"], form.cleaned_data["course_key"]
        )


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
            info = data[:8] + ".." if len(data) > 10 else data
            course_name = (
                course.display_name[:40] + ".."
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
        home_ongoing_course_dict["name"] = "On going Courses"
        home_ongoing_course_dict["value"] = ongoing_course_list
        home_ongoing_course_list.append(home_ongoing_course_dict)
        return JsonResponse(home_ongoing_course_list, status=200, safe=False)


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
            info = data[:8] + ".." if len(data) > 10 else data
            course_name = (
                course.display_name[:40] + ".."
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
            info = data[:8] + ".." if len(data) > 10 else data
            course_name = (
                course.display_name[:40] + ".."
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
                courseid.display_name_with_default[:55]
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
                courseid.display_name_with_default[:55]
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
            except:

                # user = get_authuser(user_query.id)

                result = {}
                result["Message"] = "Invalid User"
                return JsonResponse(result, status=404)
            courseid = request.GET.get("course_id").replace(" ", "+")
            course_id = CourseKey.from_string(courseid)
            user_course = sponsored_user(user, course_id)
            user_ad_view = user_ad_view_counter(user.id, course_id)

            # log.info(u"user_ad_view-> %s",user_ad_view)

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
            info = data[:8] + ".." if len(data) > 10 else data
            course_name = (
                course.display_name[:40] + ".."
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
            info = data[:8] + ".." if len(data) > 10 else data
            course_name = (
                course.display_name[:40] + ".."
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
