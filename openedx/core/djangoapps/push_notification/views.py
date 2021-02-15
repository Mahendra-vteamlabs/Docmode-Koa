# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import logging
import pytz
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.views import APIView
from util.json_request import JsonResponse

from oauth2_provider.models import AccessToken
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from student.models import UserProfile
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.push_notification.tasks import (
    send_new_message_notification,
)
from .models import DocmodeNotification, MobileDiviseDetail
from django.contrib.auth.models import User


log = logging.getLogger(__name__)


class TokenAPIView(APIView):
    """
    Token POST API
    Saves users mobile related information in UserProfile model
    """

    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    def post(self, request):
        try:
            mobile_device_token = request.POST.get("mobile_device_token", False)
            mobile_device_id = request.POST.get("mobile_device_id", False)
            mobile_version = request.POST.get("mobile_version", False)
            mobile_device_type = request.POST.get("mobile_device_type", False)
            if (
                mobile_device_token
                and mobile_device_id
                and mobile_version
                and mobile_device_type
            ):
                # save users last login
                request.user.last_login = datetime.datetime.now(pytz.UTC)
                request.user.save()

                mobile_details, created = MobileDiviseDetail.objects.get_or_create(
                    user=request.user,
                )

                mobile_details.mobile_device_token = mobile_device_token
                mobile_details.mobile_device_id = mobile_device_id
                mobile_details.mobile_device_type = mobile_device_type
                mobile_details.mobile_version = mobile_version
                mobile_details.save()

                return JsonResponse(
                    {
                        "status": "true",
                        "message": "Mobile information saved successfully!",
                    },
                    status=200,
                )
            else:
                return JsonResponse(
                    {
                        "status": "false",
                        "message": "Parameter are not valid",
                    },
                    status=200,
                )
        except Exception as e:
            log.error(e)
            return JsonResponse({"status": 400, "message": str(e)})

    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)


class ListNotificationViews(DeveloperErrorViewMixin, APIView):

    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    def post(self, request):
        try:
            log.info("get request for list notification")
            username = request.POST.get("username", False)
            notification_id = request.POST.get("notification_id", False)
            if notification_id:
                notification = DocmodeNotification.objects.filter(id=notification_id)
                notification.delete()
            if username:
                log.info("get the username for notification list")
                notifications = DocmodeNotification.objects.filter(
                    users__username=username
                )
                data = []
                for notification in notifications:
                    notification_detail = {}
                    course_key = CourseKey.from_string(str(notification.course_id))
                    course_overview = CourseOverview.objects.filter(id=course_key)
                    if course_overview:
                        course_overview = course_overview[0]
                        notification_detail["title"] = course_overview.display_name
                        notification_detail["description"] = notification.message
                        notification_detail[
                            "date"
                        ] = notification.scheduled_time.strftime(
                            "%Y-%m-%dT%H:%M:%S.%fZ"
                        )
                        notification_detail["course_id"] = str(notification.course_id)
                        notification_detail[
                            "notification_type"
                        ] = notification.redirection_type
                        notification_detail["notification_id"] = notification.id
                        data.append(notification_detail)
                log.info("data print")
                if data:
                    result = {
                        "status": "true",
                        "message": "",
                        "data": data,
                    }
                    return JsonResponse(result, status=200)
                else:
                    result = {
                        "status": "false",
                        "message": "",
                        "data": data,
                    }
                    return JsonResponse(result, status=200)
            else:
                return JsonResponse(
                    {
                        "status": "false",
                        "message": "Parameter are not valid",
                    },
                    status=200,
                )
        except Exception as e:
            log.error(e)
            return JsonResponse({"status": "false", "message": str(e)}, status=400)


class CustomLoginUserViews(APIView):
    """
    Check for user login Access Token
    """

    authentication_classes = (
        JwtAuthentication,
        OAuth2AuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    def get(self, request):
        from datetime import datetime

        try:
            if request.GET.get("user_id"):
                try:
                    user = User.objects.get(id=request.GET.get("user_id"))
                except User.DoesNotExist:
                    return JsonResponse(
                        {"status": 404, "message": "User Does Not Exits."}
                    )
                access_obj = AccessToken.objects.filter(user=user)
                if access_obj.exists():
                    if (
                        pytz.utc.localize(datetime.now())
                        <= access_obj.order_by("-id")[:1].get().expires
                    ):
                        access_obj = (
                            AccessToken.objects.filter(user=user)
                            .order_by("-id")[1:]
                            .values_list("id", flat=True)
                        )
                        AccessToken.objects.filter(pk__in=list(access_obj)).delete()
                        log.info(
                            "Successfully Login for User: {}".format(str(user.username))
                        )
                        return JsonResponse(
                            {"status": 200, "message": "Successfully Login."}
                        )
                    else:
                        log.info(
                            "Your Access Token has been expired for User: {}".format(
                                str(user.username)
                            )
                        )
                        return JsonResponse(
                            {
                                "status": 202,
                                "message": "Your Access Token has been expired.",
                            }
                        )
                else:
                    log.info(
                        "Successfully Login for User: {}".format(str(user.username))
                    )
                    return JsonResponse(
                        {"status": 200, "message": "Successfully Login."}
                    )
            else:
                return JsonResponse({"status": 404, "message": "Please Add user_id."})
        except Exception as error:
            log.error(
                "Error while CustomAuthentications. The error is {}".format(str(error))
            )
            return JsonResponse(
                {
                    "status": 404,
                    "message": "Error while CustomAuthentications, Please try again.",
                }
            )
