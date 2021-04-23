"""
Search API views
"""
import math
import json
import django
import urllib
import logging
import requests
from opaque_keys.edx.keys import CourseKey
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from util.course import get_encoded_course_sharing_utm_params, get_link_for_about_page
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Count
from search.api import course_discovery_search, course_discovery_filter_fields
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from lms.djangoapps.certificates.api import certificate_downloadable_status
from student.models import CourseEnrollment, User
from courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.specialization.models import categories
from lms.djangoapps.webform.views import webformdetails
from lms.djangoapps.reg_form.views import userdetails
from lms.djangoapps.course_extrainfo.views import (
    category_courses_count,
    category_lectures_count,
    category_casestudies_count,
    course_ctype_number,
)

# from zerobounce import ZeroBounceAPI
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from xmodule.modulestore.django import modulestore
from edxmako.shortcuts import render_to_response
from common.djangoapps.organizations.models import OrganizationCourse, Organization


@view_auth_classes(is_authenticated=False)
class CourseSearchView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        """
        Implements the GET method as described in the class docstring.
        """
        # logging.info(request.GET)
        search_key = request.GET.get("search_key")
        user_id = request.GET.get("user_id")
        # logging.info(user_id)
        size = 20000
        search_url = request.build_absolute_uri(reverse("course_discovery"))
        if "page" in request.GET:
            page = int(request.GET.get("page")) - 1
        else:
            page = 0

        if "org" in request.GET:
            if not request.GET.get("org"):
                request.GET = request.GET.copy()
                request.GET.pop("org")
        if "subjects" in request.GET:
            if not request.GET.get("subjects"):
                request.GET = request.GET.copy()
                request.GET.pop("subjects")
        if "coursetype" in request.GET:
            if not request.GET.get("coursetype"):
                request.GET = request.GET.copy()
                request.GET.pop("coursetype")

        def _process_field_values(request):
            """ Create separate dictionary of supported filter values provided """
            return {
                field_key: request.GET[field_key]
                for field_key in request.GET
                if field_key in course_discovery_filter_fields()
            }

        field_dictionary = _process_field_values(request)
        if "coursetype" in field_dictionary.keys():
            if field_dictionary["coursetype"] == "lectures":
                field_dictionary["coursetype"] = "Lectures"
            elif field_dictionary["coursetype"] == "courses":
                field_dictionary["coursetype"] = "Courses"

        results = course_discovery_search(
            search_term=search_key,
            size=size,
            from_=0,
            field_dictionary=field_dictionary,
        )
        if results.get("total"):
            # logging.info("for search api have results")
            result = []
            course_ids = []
            for course in results.get("results"):
                course_id = course.get("_id")
                course_key = CourseKey.from_string(course_id)
                course_ids.append(course_key)
            course_overviews = CourseOverview.objects.filter(
                id__in=course_ids
            ).order_by("-start")
            starting = (page) * 20
            ending = (page + 1) * (20)
            # logging.info("course start index [%s]", course_ids)
            course_overviews = course_overviews[starting:ending]
            # logging.info("courses list [%s]", course_overviews)
            for course_overview in course_overviews:
                search_course = {}
                course_id = str(course_overview.id)
                # logging.info("finding response for [%s]", course_id)
                course_key = CourseKey.from_string(course_id)
                course_extra_info = course_extrainfo.objects.get(course_id=course_key)
                # logging.info("user [%s]", user_id)
                course_enroll = CourseEnrollment.objects.filter(
                    course_id=course_key, user_id=user_id
                )
                # logging.info(course_enroll)
                if course_enroll.exists():
                    # logging.info("course enrollment exist")
                    search_course["is_enrolled"] = "true"
                    if course_extra_info.course_type == "2":
                        video_blocks_in_course = modulestore().get_items(
                            course_key, qualifiers={"category": "video"}
                        )
                        block_id = modulestore().get_items(
                            course_key, qualifiers={"category": "video"}
                        )
                        if block_id:
                            data = block_id[0].__dict__
                            if "scope_ids" in data:
                                search_course["seq_block_id"] = data.get(
                                    "scope_ids"
                                ).def_id.to_deprecated_string()
                            else:
                                search_course["seq_block_id"] = ""
                        else:
                            search_course["seq_block_id"] = ""
                        if video_blocks_in_course:
                            # logging.info(video_blocks_in_course)
                            # logging.info("video_block_in_course successfully printes")
                            # logging.info(video_blocks_in_course[0])
                            # logging.info("video_block_in_course[0] successfully printes")
                            video_id = (
                                video_blocks_in_course[0].youtube_id_1_25
                                or video_blocks_in_course[0].youtube_id_0_75
                                or video_blocks_in_course[0].youtube_id_1_0
                                or video_blocks_in_course[0].youtube_id_1_25
                                or video_blocks_in_course[0].youtube_id_1_5
                            )
                            if video_id:
                                search_course["video_url"] = (
                                    "https://www.youtube.com/watch?v=" + video_id
                                )
                            else:
                                search_course["video_url"] = ""
                        else:
                            search_course["video_url"] = ""
                    else:
                        search_course["video_url"] = ""
                else:
                    search_course["video_url"] = ""
                    search_course["seq_block_id"] = ""
                    search_course["is_enrolled"] = "false"
                if course_extra_info.course_type == "2":
                    search_course["is_lecture"] = "true"
                else:
                    search_course["is_lecture"] = "false"
                search_course["wp_url"] = course_extra_info.course_seo_url
                search_course["id"] = course_id
                search_course["media"] = {
                    "course_image": {"uri": course_overview.course_image_url},
                    "course_video": {"uri": course_overview.course_video_url},
                }
                search_course["name"] = course_overview.display_name
                search_course["number"] = course_overview.number
                search_course["org"] = course_overview.org
                search_course["start_display"] = course_overview.start_display
                search_course["start_type"] = course_overview.start_type
                search_course["short_description"] = course_overview.short_description
                search_course["pacing"] = course_overview.pacing
                search_course["mobile_available"] = course_overview.mobile_available
                search_course["invitation_only"] = course_overview.invitation_only
                search_course["start"] = (
                    course_overview.start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if course_overview.start
                    else course_overview.start
                )
                search_course["end"] = (
                    course_overview.end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if course_overview.end
                    else course_overview.end
                )
                catalog_visibility = course_overview.catalog_visibility
                if catalog_visibility in ["about", "none"]:
                    hidden = True
                else:
                    hidden = False
                search_course["hidden"] = hidden
                base_url = "?".join(
                    [
                        reverse("blocks_in_course"),
                        urllib.urlencode({"course_id": course_id}),
                    ]
                )
                block_url = self.request.build_absolute_uri(base_url)
                search_course["blocks_url"] = block_url
                search_course["course_id"] = course_id
                # logging.info("succesfully find response for [%s]", course_id)
                result.append(search_course)
            results["results"] = result
            page = page + 1
            if page > 1:
                pages = page - 1
                previous = (
                    settings.LMS_ROOT_URL
                    + "/api/v1/course/search/discovery/?search_key={search_key}&user_id={user_id}&page={page}".format(
                        search_key=search_key, user_id=user_id, page=pages
                    )
                )
            else:
                previous = ""
            if results.get("total") > page * 20:
                results["pagination"] = {
                    "count": results.get("total"),
                    "previous": previous,
                    "num_pages": math.ceil(results.get("total") / float(size)),
                    "next": settings.LMS_ROOT_URL
                    + "/api/v1/course/search/discovery/?search_key={search_key}&user_id={user_id}&page={page}".format(
                        search_key=search_key, user_id=user_id, page=page
                    ),
                }
            else:
                results["pagination"] = {
                    "count": results.get("total"),
                    "previous": previous,
                    "num_pages": math.ceil(results.get("total") / float(size)),
                    "next": "",
                }

            results["Access-Control-Allow-Origin"] = "*"
            response = JsonResponse(results, status=200)
            return response
        else:
            res = {}
            res["pagination"] = {"count": 0, "previous": "", "num_pages": 0, "next": ""}
            res["facets"] = {}
            res["results"] = []
            res["total"] = 0
            res["max_score"] = 0
            res["Access-Control-Allow-Origin"] = "*"
            response = JsonResponse(res, status=200)
            return response


@view_auth_classes(is_authenticated=False)
class CourseCategoryView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):

        category_list = []
        category_dict = {}
        search_key = request.GET.get("search_key")
        user_id = request.GET.get("user_id")
        size = 200
        search_url = request.build_absolute_uri(reverse("course_discovery"))

        if "org" in request.GET:
            if not request.GET.get("org"):
                request.GET = request.GET.copy()
                request.GET.pop("org")
        if "subjects" in request.GET:
            if not request.GET.get("subjects"):
                request.GET = request.GET.copy()
                request.GET.pop("subjects")
        if "coursetype" in request.GET:
            if not request.GET.get("coursetype"):
                request.GET = request.GET.copy()
                request.GET.pop("coursetype")

        def _process_field_values(request):
            """ Create separate dictionary of supported filter values provided """
            return {
                field_key: request.GET[field_key]
                for field_key in request.GET
                if field_key in course_discovery_filter_fields()
            }

        field_dictionary = _process_field_values(request)
        if "coursetype" in field_dictionary.keys():
            if field_dictionary["coursetype"] == "lectures":
                field_dictionary["coursetype"] = "Lectures"
            elif field_dictionary["coursetype"] == "courses":
                field_dictionary["coursetype"] = "Courses"
        # logging.info(field_dictionary)
        results = course_discovery_search(
            search_term=search_key,
            size=size,
            from_=0,
            field_dictionary=field_dictionary,
        )
        # logging.info(results)
        associations_list = results["facets"]["org"]["terms"]
        topics_list = results["facets"]["subjects"]["terms"]
        association_list = []
        if associations_list:
            for name, count in associations_list.items():
                association_dict = {}
                association_dict["name"] = name
                association_dict["count"] = count
                association_list.append(association_dict)
        else:
            association_list = []
        topic_list = []
        if topics_list:
            for name, count in topics_list.items():
                topic_dict = {}
                topic_dict["name"] = name
                topic_dict["count"] = count
                topic_list.append(topic_dict)
        else:
            topic_list = []

        cat_course_count = (
            course_extrainfo.objects.exclude(category="")
            .values("category")
            .annotate(ccount=Count("category"))
            .filter(ccount__gte=1)
            .order_by("-ccount")
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
                if category["topic_name"] not in topic_list:
                    category_dict = {}
                    category_dict["name"] = category["topic_name"]
                    # category_dict['topic_url'] = "https://learn.docmode.org/api/v1/wp_course/search/discovery/?coursetype=Lectures&subjects="+category['topic_name']
                    if courses_count:
                        count = courses_count[0]["ccount"]
                    if lectures_count:
                        count = lectures_count[0]["ccount"]

                    topics_list.update({category["topic_name"]: count})
        else:
            categories_list = []

        # topics_list.append(category_dict)

        association_topic_list = []
        association_topic_dict = {}
        association_topic_dict["name"] = "Association"
        association_topic_dict["value"] = association_list
        association_topic_list.append(association_topic_dict)
        association_topic_dict = {}
        association_topic_dict["name"] = "Topics"
        association_topic_dict["value"] = topics_list
        association_topic_list.append(association_topic_dict)
        # association_topic_dict = {}
        # association_topic_dict['name'] = "Topics course/lecture count"
        # association_topic_dict['value'] = category_list
        # association_topic_list.append(association_topic_dict)
        return JsonResponse(association_topic_list, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class CourseSearchEnrollmentView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        """
        Implements the GET method as described in the class docstring.
        """
        from rest_framework.reverse import reverse

        params = request.GET
        search_key = request.GET.get("search_key")
        course_category = request.GET.get("subjects")
        org = request.GET.get("org")
        user_id = request.GET.get("user_id")
        size = 2000
        if "org" in request.GET:
            if not request.GET.get("org"):
                request.GET = request.GET.copy()
                request.GET.pop("org")
        if "subjects" in request.GET:
            if not request.GET.get("subjects"):
                request.GET = request.GET.copy()
                request.GET.pop("subjects")
        search_url = request.build_absolute_uri(reverse("course_discovery"))
        if course_category or org:

            def _process_field_values(request):
                """ Create separate dictionary of supported filter values provided """
                return {
                    field_key: request.GET[field_key]
                    for field_key in request.GET
                    if field_key in course_discovery_filter_fields()
                }

            field_dictionary = _process_field_values(request)
            if "coursetype" in field_dictionary.keys():
                if field_dictionary["coursetype"] == "lectures":
                    field_dictionary["coursetype"] = "Lectures"
                elif field_dictionary["coursetype"] == "courses":
                    field_dictionary["coursetype"] = "Courses"
            results = course_discovery_search(
                search_term=search_key,
                size=size,
                from_=0,
                field_dictionary=field_dictionary,
            )
        else:

            def _process_field_values(request):
                """ Create separate dictionary of supported filter values provided """
                return {
                    field_key: request.POST[field_key]
                    for field_key in request.POST
                    if field_key in course_discovery_filter_fields()
                }

            field_dictionary = _process_field_values(request)
            if "coursetype" in field_dictionary.keys():
                if field_dictionary["coursetype"] == "lectures":
                    field_dictionary["coursetype"] = "Lectures"
                elif field_dictionary["coursetype"] == "courses":
                    field_dictionary["coursetype"] = "Courses"
            if search_key:
                results = course_discovery_search(
                    search_term=search_key,
                    size=size,
                    from_=0,
                    field_dictionary=field_dictionary,
                )
            else:
                results = course_discovery_search(
                    size=size,
                    from_=0,
                    field_dictionary=field_dictionary,
                )
        if results.get("total"):
            # logging.info("for search api have results")
            result = []
            course_ids = []
            for course in results.get("results"):
                course_id = course.get("_id")
                course_key = CourseKey.from_string(course_id)
                course_ids.append(course_key)
            course_overviews = CourseOverview.objects.filter(
                id__in=course_ids
            ).order_by("-start")
            # logging.info("courses list [%s]", course_overviews)
            course_search_enroll = []
            for course_overview in course_overviews:
                search_course = {}
                course_id = str(course_overview.id)
                course_key = CourseKey.from_string(course_id)
                course_enroll = CourseEnrollment.objects.filter(
                    course_id=course_key, user_id=user_id, is_active=True
                )
                if course_enroll.exists():
                    course_enroll = course_enroll[0]
                    try:
                        user = User.objects.get(id=user_id)
                    except:
                        message = {
                            "error": _('Does not match user for "{user_id}"').format(
                                user_id=user_id
                            )
                        }
                        response = JsonResponse(
                            {"status": "false", "message": message}, status=400
                        )
                        return response
                    search_course["mode"] = course_enroll.mode
                    search_course["is_active"] = course_enroll.is_active
                    created = course_enroll.created
                    created = created.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    search_course["created"] = created
                    certificate_info = certificate_downloadable_status(user, course_key)
                    if certificate_info["is_downloadable"]:
                        certificates = {
                            "url": request.build_absolute_uri(
                                certificate_info["download_url"]
                            ),
                        }
                    else:
                        certificates = {}
                    search_course["certificate"] = certificates
                    block_id = modulestore().get_items(
                        course_key, qualifiers={"category": "video"}
                    )
                    if block_id:
                        data = block_id[0].__dict__
                        if "scope_ids" in data:
                            seq_block_id = data.get(
                                "scope_ids"
                            ).def_id.to_deprecated_string()
                        else:
                            seq_block_id = ""
                    else:
                        seq_block_id = ""

                    course_extra_info = course_extrainfo.objects.get(
                        course_id=course_key
                    )
                    if course_extra_info.course_type == "2":
                        video_blocks_in_course = modulestore().get_items(
                            course_key, qualifiers={"category": "video"}
                        )
                        if video_blocks_in_course:
                            video_id = (
                                video_blocks_in_course[0].youtube_id_1_25
                                or video_blocks_in_course[0].youtube_id_0_75
                                or video_blocks_in_course[0].youtube_id_1_0
                            )
                            if video_id:
                                video_url = (
                                    "https://www.youtube.com/watch?v=" + video_id
                                )
                            else:
                                video_url = ""
                        else:
                            video_url = ""
                        is_lecture = "true"
                    else:
                        video_url = ""
                        is_lecture = "false"
                    start_date = course_overview.start
                    start = start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    end_date = course_overview.end
                    if end_date:
                        end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    search_course["course"] = {
                        "id": course_id,
                        "is_lecture": is_lecture,
                        "video_url": video_url,
                        "seq_block_id": seq_block_id,
                        "number": course_overview.display_number_with_default,
                        "name": course_overview.display_name,
                        "org": course_overview.display_org_with_default,
                        # dates
                        "start": start,
                        "start_display": course_overview.start_display,
                        "start_type": course_overview.start_type,
                        "end": end_date,
                        # notification info
                        "subscription_id": course_overview.clean_id(padding_char="_"),
                        # access info
                        "courseware_access": has_access(
                            user, "load_mobile", course_overview
                        ).to_json(),
                        # various URLs
                        # course_image is sent in both new and old formats
                        # (within media to be compatible with the new Course API)
                        "media": {
                            "course_image": {
                                "uri": course_overview.course_image_url,
                                "name": "Course Image",
                            }
                        },
                        "course_image": course_overview.course_image_url,
                        "course_about": get_link_for_about_page(course_overview),
                        "course_sharing_utm_parameters": get_encoded_course_sharing_utm_params(),
                        "course_updates": reverse(
                            "course-updates-list",
                            kwargs={"course_id": course_id},
                            request=request,
                        ),
                        "course_handouts": reverse(
                            "course-handouts-list",
                            kwargs={"course_id": course_id},
                            request=request,
                        ),
                        "discussion_url": reverse(
                            "discussion_course",
                            kwargs={"course_id": course_id},
                            request=request,
                        )
                        if course_overview.is_discussion_tab_enabled()
                        else None,
                        "video_outline": reverse(
                            "video-summary-list",
                            kwargs={"course_id": course_id},
                            request=request,
                        ),
                    }
                    course_search_enroll.append(search_course)
            if not course_search_enroll:
                course_search_enroll = []
                return JsonResponse(course_search_enroll, status=200, safe=False)
            return JsonResponse(course_search_enroll, status=200, safe=False)
        else:
            course_search_enroll = []
            return JsonResponse(course_search_enroll, status=200, safe=False)


@view_auth_classes(is_authenticated=False)
class CourseCheckcourseWebinarView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        from lms.djangoapps.webform.views import webformdetails

        if "course_id" in request.GET:
            course_id = request.GET.get("course_id")
            # logging.info(course_id)
        else:
            message = _("course_id paramater missing")
            result = {}
            result["Data"] = {}
            result["Status"] = "false"
            result["Message"] = message
            return JsonResponse(result, status=404)
        userstate = ""
        if "user" in request.GET:
            user_name = request.GET.get("user")
            try:
                user = User.objects.get(username=user_name)
                try:
                    userid = userdetails(user)
                    userstate = userid.rcity
                except userdetails.DoesNotExist:
                    pass
            except User.DoesNotExist:
                result = {}
                message = _("User not found for username %s" % (user_name))
                result["Data"] = {}
                result["Status"] = "false"
                result["Message"] = message
                return JsonResponse(result, status=404)
        else:
            result = {}
            message = _("user Parameter Missing")
            result["Data"] = {}
            result["Status"] = "false"
            result["Message"] = message
            return JsonResponse(result, status=400)
        qnadetails = webformdetails(course_id)
        result = {}
        if qnadetails and qnadetails.feedback_form_link:
            if qnadetails.feedback_form_link == "NULL":
                feedback_url = ""
            else:
                feedback_url = qnadetails.feedback_form_link
        else:
            feedback_url = ""
        if qnadetails:
            data = {}
            if userstate:
                data = {
                    "city": userstate,
                    "show_webinar": "true",
                    "feedback_url": feedback_url,
                }
                message = ""
                result["Data"] = data
                result["Status"] = "true"
                result["Message"] = message
            return JsonResponse(result, status=200, safe=False)
        else:
            message = {"error": _("Course not found in webinar")}
            data = {}
            if userstate:
                data = {
                    "city": userstate,
                    "show_webinar": "false",
                    "feedback_url": feedback_url,
                }
                message = ""
                result["Data"] = data
                result["Status"] = "true"
                result["Message"] = message
            return JsonResponse(result, status=200)


@view_auth_classes(is_authenticated=False)
class CourseWebinarView(DeveloperErrorViewMixin, APIView):

    authentication_classes = JwtAuthentication
    permission_classes = ApiKeyHeaderPermissionIsAuthenticated

    def post(self, request):
        from lms.djangoapps.webform.views import webformdetails

        course_id = request.POST.get("course_id")
        # logging.info(course_id)
        qnadetails = webformdetails(course_id)
        url = qnadetails.sheeturl
        name = request.POST.get("name")
        location = request.POST.get("location")
        question = request.POST.get("question")
        if not name or not location or not question:
            message = {"error": _("Missing Parameter")}
            return JsonResponse({"status": "false", "message": message}, status=400)
        data = {
            "entry.%s" % (qnadetails.name): name,
            "entry.%s" % (qnadetails.location): location,
            "entry.%s" % (qnadetails.question): question,
        }
        try:
            result = requests.post(url=url, data=data)
            if result.status_code == 200:
                return JsonResponse({"status": "true"}, status=200)
            else:
                message = {"error": _("google form not submit something happen")}
                return JsonResponse({"status": "false", "message": message}, status=400)
        except:
            message = {"error": _("google form not submit something happen")}
            return JsonResponse({"status": "false", "message": message}, status=400)


@view_auth_classes(is_authenticated=False)
class UserEmailValidationView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        emailid = request.GET.get("email_id")
        zba = ZeroBounceAPI("af8e53a08b7a4a9ab3cc98584fd3a734")
        zerobounce_resp = zba.validate(emailid)
        # logging.info(zerobounce_resp.status)
        if zerobounce_resp.status == "Valid":
            message = ""
            return JsonResponse({"status": "true", "message": message}, status=200)
        else:
            message = "Email id is not valid"
            return JsonResponse({"status": "false", "message": message}, status=200)


@view_auth_classes(is_authenticated=False)
class DocmodePrivacyView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        return render_to_response("static_templates/docmode_privacy.html", None)


@view_auth_classes(is_authenticated=False)
class DocmodeTosView(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        return render_to_response("static_templates/docmode_tos.html", None)


@view_auth_classes(is_authenticated=False)
class CourseSearchView_local(DeveloperErrorViewMixin, APIView):
    def get(self, request, **kwargs):
        """
        Implements the GET method as described in the class docstring.
        """
        # logging.info(request.GET)
        search_key = request.GET.get("search_key")
        user_id = request.GET.get("user_id")
        # logging.info(user_id)
        size = 20000
        search_url = request.build_absolute_uri(reverse("course_discovery"))
        if "page" in request.GET:
            page = int(request.GET.get("page")) - 1
        else:
            page = 0

        if "org" in request.GET:
            if not request.GET.get("org"):
                request.GET = request.GET.copy()
                request.GET.pop("org")
        if "subjects" in request.GET:
            if not request.GET.get("subjects"):
                request.GET = request.GET.copy()
                request.GET.pop("subjects")
        if "coursetype" in request.GET:
            if not request.GET.get("coursetype"):
                request.GET = request.GET.copy()
                request.GET.pop("coursetype")

        def _process_field_values(request):
            """ Create separate dictionary of supported filter values provided """
            return {
                field_key: request.GET[field_key]
                for field_key in request.GET
                if field_key in course_discovery_filter_fields()
            }

        field_dictionary = _process_field_values(request)
        if "coursetype" in field_dictionary.keys():
            if field_dictionary["coursetype"] == "lectures":
                field_dictionary["coursetype"] = "Lectures"
            elif field_dictionary["coursetype"] == "courses":
                field_dictionary["coursetype"] = "Courses"
        results = course_discovery_search(
            search_term=search_key,
            size=size,
            from_=0,
            field_dictionary=field_dictionary,
        )
        if results.get("total"):
            # logging.info("for search api have results")
            result = []
            course_ids = []
            for course in results.get("results"):
                course_id = course.get("_id")
                course_key = CourseKey.from_string(course_id)
                course_ids.append(course_key)
            course_overviews = CourseOverview.objects.filter(
                id__in=course_ids
            ).order_by("-start")
            starting = (page) * 20
            ending = (page + 1) * (20)
            # logging.info("course start index [%s]", course_ids)
            course_overviews = course_overviews[starting:ending]
            # logging.info("courses list [%s]", course_overviews)
            for course_overview in course_overviews:
                search_course = {}
                course_id = str(course_overview.id)
                # logging.info("finding response for [%s]", course_id)
                course_key = CourseKey.from_string(course_id)
                course_extra_info = course_extrainfo.objects.get(course_id=course_key)
                # logging.info("user [%s]", user_id)
                course_enroll = CourseEnrollment.objects.filter(
                    course_id=course_key, user_id=user_id
                )
                # logging.info(course_enroll)
                if course_enroll.exists():
                    # logging.info("course enrollment exist")
                    search_course["is_enrolled"] = "true"
                    if course_extra_info.course_type == "2":
                        video_blocks_in_course = modulestore().get_items(
                            course_key, qualifiers={"category": "video"}
                        )
                        block_id = modulestore().get_items(
                            course_key, qualifiers={"category": "video"}
                        )
                        if block_id:
                            data = block_id[0].__dict__
                            if "scope_ids" in data:
                                search_course["seq_block_id"] = data.get(
                                    "scope_ids"
                                ).def_id.to_deprecated_string()
                            else:
                                search_course["seq_block_id"] = ""
                        else:
                            search_course["seq_block_id"] = ""
                        if video_blocks_in_course:
                            # logging.info(video_blocks_in_course)
                            # logging.info("video_block_in_course successfully printes")
                            # logging.info(video_blocks_in_course[0])
                            # logging.info("video_block_in_course[0] successfully printes")
                            video_id = (
                                video_blocks_in_course[0].youtube_id_1_25
                                or video_blocks_in_course[0].youtube_id_0_75
                                or video_blocks_in_course[0].youtube_id_1_0
                                or video_blocks_in_course[0].youtube_id_1_25
                                or video_blocks_in_course[0].youtube_id_1_5
                            )
                            if video_id:
                                search_course["video_url"] = (
                                    "https://www.youtube.com/watch?v=" + video_id
                                )
                            else:
                                search_course["video_url"] = ""
                        else:
                            search_course["video_url"] = ""
                    else:
                        search_course["video_url"] = ""
                else:
                    search_course["video_url"] = ""
                    search_course["seq_block_id"] = ""
                    search_course["is_enrolled"] = "false"
                if course_extra_info.course_type == "2":
                    search_course["is_lecture"] = "true"
                else:
                    search_course["is_lecture"] = "false"
                search_course["wp_url"] = course_extra_info.course_seo_url
                search_course["id"] = course_id
                search_course["media"] = {
                    "course_image": {"uri": course_overview.course_image_url},
                    "course_video": {"uri": course_overview.course_video_url},
                }
                search_course["name"] = course_overview.display_name
                search_course["number"] = course_overview.number
                search_course["org"] = course_overview.org
                search_course["start_display"] = course_overview.start_display
                search_course["start_type"] = course_overview.start_type
                search_course["short_description"] = course_overview.short_description
                search_course["pacing"] = course_overview.pacing
                search_course["mobile_available"] = course_overview.mobile_available
                search_course["invitation_only"] = course_overview.invitation_only
                search_course["start"] = (
                    course_overview.start.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if course_overview.start
                    else course_overview.start
                )
                search_course["end"] = (
                    course_overview.end.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if course_overview.end
                    else course_overview.end
                )
                catalog_visibility = course_overview.catalog_visibility
                if catalog_visibility in ["about", "none"]:
                    hidden = True
                else:
                    hidden = False
                search_course["hidden"] = hidden
                base_url = "?".join(
                    [
                        reverse("blocks_in_course"),
                        urllib.urlencode({"course_id": course_id}),
                    ]
                )
                block_url = self.request.build_absolute_uri(base_url)
                search_course["blocks_url"] = block_url
                search_course["course_id"] = course_id
                # logging.info("succesfully find response for [%s]", course_id)
                result.append(search_course)
            associations_list = results["facets"]["org"]["terms"]
            topics_list = results["facets"]["subjects"]["terms"]
            if "org" not in request.GET and "subjects" not in request.GET:
                if request.GET.get("coursetype") == "Lectures":
                    course_ids = course_extrainfo.objects.filter(course_type=2).values()
                else:
                    course_ids = course_extrainfo.objects.filter(course_type=1).values()
                cid = []
                for courseid in course_ids:
                    course_id = CourseKey.from_string(courseid["course_id"])
                    cid.append(course_id)
                course_data = (
                    CourseOverview.objects.filter(pk__in=cid, catalog_visibility="both")
                    .values("org")
                    .annotate(ccount=Count("org"))
                )

                for course in course_data:
                    if course["org"] not in associations_list:
                        if course["ccount"] > 0:
                            results["facets"]["org"]["terms"].update(
                                {course["org"]: course["ccount"]}
                            )

                if request.GET.get("coursetype") == "Lectures":
                    cat_course_count = (
                        course_extrainfo.objects.filter(course_type=2)
                        .exclude(category="")
                        .values("category")
                        .annotate(ccount=Count("category"))
                        .filter(ccount__gte=1)
                        .order_by("-ccount")
                    )
                else:
                    cat_course_count = (
                        course_extrainfo.objects.filter(course_type=1)
                        .exclude(category="")
                        .values("category")
                        .annotate(ccount=Count("category"))
                        .filter(ccount__gte=1)
                        .order_by("-ccount")
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
                        if category["topic_name"] not in topics_list:
                            category_dict = {}
                            category_dict["name"] = category["topic_name"]
                            # category_dict['topic_url'] = "https://learn.docmode.org/api/v1/wp_course/search/discovery/?coursetype=Lectures&subjects="+category['topic_name']
                            if courses_count:
                                count = courses_count[0]["ccount"]
                            if lectures_count:
                                count = lectures_count[0]["ccount"]

                            results["facets"]["subjects"]["terms"].update(
                                {category["topic_name"]: count}
                            )

            associations_total_list = results["facets"]["org"]["terms"]
            # results['facets']['org']['terms'].clear()
            # logging.info(u"og1_assoc %s", associations_total_list)
            org_data = Organization.objects.filter(marketing_display=1).values()
            org_list = []
            for org in org_data:
                org_list.append(org["short_name"])
            dicts = {}
            for assoc in associations_total_list:
                if assoc in org_list:
                    dicts[assoc] = associations_total_list[assoc]

            results["facets"]["org"]["terms"] = dicts

            logging.info(u"f3_assoc %s", dicts)
            # results['facets']['org']['terms'].clear()
            # results['facets']['org']['terms'].update(associations_total_list)

            results["results"] = result
            page = page + 1
            if page > 1:
                pages = page - 1
                previous = (
                    settings.LMS_ROOT_URL
                    + "/api/v1/course/search/discovery_local/?search_key={search_key}&user_id={user_id}&page={page}".format(
                        search_key=search_key, user_id=user_id, page=pages
                    )
                )
            else:
                previous = ""
            if results.get("total") > page * 20:
                results["pagination"] = {
                    "count": results.get("total"),
                    "previous": previous,
                    "num_pages": math.ceil(results.get("total") / float(size)),
                    "next": settings.LMS_ROOT_URL
                    + "/api/v1/course/search/discovery_local/?search_key={search_key}&user_id={user_id}&page={page}".format(
                        search_key=search_key, user_id=user_id, page=page
                    ),
                }
            else:
                results["pagination"] = {
                    "count": results.get("total"),
                    "previous": previous,
                    "num_pages": math.ceil(results.get("total") / float(size)),
                    "next": "",
                }

            results["Access-Control-Allow-Origin"] = "*"
            response = JsonResponse(results, status=200)
            return response
        else:
            res = {}
            res["pagination"] = {"count": 0, "previous": "", "num_pages": 0, "next": ""}
            res["facets"] = {}
            res["results"] = []
            res["total"] = 0
            res["max_score"] = 0
            res["Access-Control-Allow-Origin"] = "*"
            response = JsonResponse(res, status=200)
            return response
