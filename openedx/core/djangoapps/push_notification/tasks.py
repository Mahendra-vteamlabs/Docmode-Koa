"""
This file contains celery tasks for create bulk user registration
"""
import json
from datetime import datetime, timedelta
import logging
from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from student.models import UserProfile, CourseEnrollment
import re
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .models import (
    DocmodeNotification,
    DocmodeNotificationCourse,
    DocmodeNotificationEmail,
)
from student.models import CourseEnrollment
import requests
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from pyfcm import FCMNotification

log = logging.getLogger("edx.celery.task")

from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.course_extrainfo.models import course_extrainfo
from lms.djangoapps.specialization.models import categories
from lms.djangoapps.reg_form.models import extrafields
from openedx.core.djangoapps.push_notification.models import MobileDiviseDetail


@task(bind=True)
def send_new_message_notification(self, values):

    log.info("get the request from command ")
    for value in values:
        courses = value.get("course_id")
        redirection_type = value.get("redirection_type")
        try:
            for course in courses:
                message = ""
                title = ""
                course = CourseKey.from_string(course)
                course_obj = CourseOverview.objects.filter(id=course)
                course_extra_categoey_id = course_extrainfo.objects.filter(
                    course_id=str(course)
                )
                # log.info("notification for course %s",course)
                if redirection_type == "start_date":
                    if course_extra_categoey_id:
                        if course_extra_categoey_id.course_type == "2":
                            title = "Today Lecture Start"
                        else:
                            title = "Today Course Start"
                    if course_obj:
                        message = course_obj[0].display_name + " Starts Today!"
                if redirection_type == "before_days":
                    if course_extra_categoey_id:
                        if course_extra_categoey_id.course_type == "2":
                            title = "Lecture Start Soon"
                        else:
                            title = "Course Start Soon"
                    if course_obj:
                        message = course_obj[0].display_name + " Starts Soon!"
                if redirection_type == "course_created":
                    if course_obj:
                        message = (
                            " Announcing a new run of " + course_obj[0].display_name
                        )
                        title = "Announcement of a new course/lecture"
                if redirection_type == "course_created":
                    course_extra_categoey_id = course_extrainfo.objects.filter(
                        course_id=str(course)
                    )
                    if course_extra_categoey_id:
                        category_id = course_extra_categoey_id[0].category
                        category_specialization_ids = list(
                            categories.objects.filter(id=category_id).values_list(
                                "topic_specialization", flat=True
                            )
                        )
                        if category_specialization_ids:
                            specialization_match_users_list = list(
                                extrafields.objects.filter(
                                    specialization__in=category_specialization_ids
                                ).values_list("user__id", flat=True)
                            )
                            users = User.objects.filter(
                                id__in=specialization_match_users_list
                            )
                        else:
                            users = []
                    else:
                        users = []
                else:
                    enroll = list(
                        CourseEnrollment.objects.filter(
                            course_id=course, is_active=True
                        ).values_list("user_id", flat=True)
                    )
                    users = User.objects.filter(id__in=enroll)
                log.info("users are %s", users)
                if users:
                    for user in users:
                        log.info("user is %s", user)
                        notifiction_obj = DocmodeNotification()
                        notifiction_obj.status = "draft"
                        notifiction_obj.course_id = str(course)
                        notifiction_obj.save()
                        andriod_registration_ids = list(
                            MobileDiviseDetail.objects.filter(
                                user_id=user.id, mobile_device_type="android"
                            ).values_list(("mobile_device_token"), flat=True)
                        )
                        iphone_registration_ids = list(
                            MobileDiviseDetail.objects.filter(
                                user=user, mobile_device_type="ios"
                            ).values_list(("mobile_device_token"), flat=True)
                        )
                        registration_ids = []
                        push_service = FCMNotification(
                            api_key="AAAAMxle0JY:APA91bGBSOAyvMevwQfOa9TwsyBcNk1pG0LJkVGqqdUCf6DCkecC0MUYKyIv8AoGc1GD_fD5agNhZlzZF8FLoSYqv6kB7ey2nLT6Ei7O3LmNJgrVP7qqlRyIHvV8U-Q9Cw08nv8To9Xt"
                        )
                        notifiction_obj.status = "running"
                        notifiction_obj.title = title
                        notifiction_obj.message = message
                        notifiction_obj.users = user
                        notifiction_obj.redirection_type = redirection_type
                        notifiction_obj.save()
                        # log.info('Notification save in table and status is runimg')

                        fcm_url = "https://fcm.googleapis.com/fcm/send"
                        fcm_headers = {
                            "Content-Type": "application/json",
                            "Authorization": "key="
                            + "AAAAMxle0JY:APA91bGBSOAyvMevwQfOa9TwsyBcNk1pG0LJkVGqqdUCf6DCkecC0MUYKyIv8AoGc1GD_fD5agNhZlzZF8FLoSYqv6kB7ey2nLT6Ei7O3LmNJgrVP7qqlRyIHvV8U-Q9Cw08nv8To9Xt",
                        }
                        andriod_data = {
                            "message_title": title,
                            "message_body": message,
                            "course_id": str(course),
                            "notification_id": notifiction_obj.id,
                            "redirection_type": redirection_type,
                        }
                        if iphone_registration_ids:
                            iphone_data = {
                                "registration_ids": iphone_registration_ids,
                                "content_available": True,
                                "mutable_content": True,
                                "data": {
                                    "message": title,
                                    "redirection_type": redirection_type,
                                    "model_id": "",
                                    "image_url": "",
                                    "course_id": str(course),
                                    "notification_id": notifiction_obj.id,
                                },
                                "notification": {
                                    "title": title,
                                    "body": message,
                                    "sound": "default",
                                },
                            }
                        else:
                            iphone_data = {}
                        # log.info("sending notification both mobile type ")
                        # log.info("android notification user for this course %s",andriod_registration_ids)
                        # log.info("iphone notification user for this course %s",iphone_registration_ids)
                        if andriod_registration_ids:
                            result_android = push_service.notify_multiple_devices(
                                registration_ids=andriod_registration_ids,
                                data_message=andriod_data,
                            )
                            if result_android.get("success", 0) == 1:
                                log.info("iphone result %s", result_android)
                                if not DocmodeNotificationCourse.objects.filter(
                                    course_id=str(course)
                                ):
                                    notification_obj_course = (
                                        DocmodeNotificationCourse()
                                    )
                                    notification_obj_course.course_id = str(course)
                                    notification_obj_course.redirection_type = (
                                        redirection_type
                                    )
                                    notification_obj_course.scheduled_time = (
                                        datetime.now()
                                    )
                                    notification_obj_course.status = "sent"
                                    notification_obj_course.save()
                                notifiction_obj.status = "sent"
                                notifiction_obj.scheduled_time = datetime.now()
                                notifiction_obj.save()
                                log.info(
                                    '"%s" Notification send in android successfully',
                                    title,
                                )
                            else:
                                notifiction_obj.status = "error"
                                notifiction_obj.scheduled_time = datetime.now()
                                notifiction_obj.save()
                                log.info(
                                    '"%s" Notification send in android not successfully',
                                    title,
                                )
                        elif iphone_data:
                            result_iphone = requests.post(
                                fcm_url,
                                data=json.dumps(iphone_data),
                                headers=fcm_headers,
                            )
                            if result_iphone.status_code == 200:
                                if not DocmodeNotificationCourse.objects.filter(
                                    course_id=str(course)
                                ):
                                    notification_obj_course = (
                                        DocmodeNotificationCourse()
                                    )
                                    notification_obj_course.course_id = str(course)
                                    notification_obj_course.redirection_type = (
                                        redirection_type
                                    )
                                    notification_obj_course.scheduled_time = (
                                        datetime.now()
                                    )
                                    notification_obj_course.status = "sent"
                                    notification_obj_course.save()
                                log.info("iphone result %s", result_iphone)
                                notifiction_obj.status = "sent"
                                notifiction_obj.scheduled_time = datetime.now()
                                notifiction_obj.save()
                                log.info(
                                    '"%s" Notification send in iphone successfully',
                                    title,
                                )
                            else:
                                notifiction_obj.status = "error"
                                notifiction_obj.scheduled_time = datetime.now()
                                notifiction_obj.save()
                                log.info(
                                    '"%s" Notification send in iphone not successfully',
                                    title,
                                )
                        else:
                            notifiction_obj.delete()
        except Exception as e:  # pylint: disable=bare-except
            log.exception("Unable to send Notification ID", exc_info=True)


@task(bind=True)
def send_new_message_notification_email(self, values):

    log.info("get the request from command for email")
    for value in values:
        courses = value.get("course_id")
        redirection_type = value.get("redirection_type")
        from pytz import timezone

        try:
            for course in courses:
                notifiction_obj_email = DocmodeNotificationEmail()
                notifiction_obj_email.status = "draft"
                notifiction_obj_email.course_id = str(course)
                notifiction_obj_email.save()
                message = ""
                course = CourseKey.from_string(course)
                course_obj = CourseOverview.objects.filter(id=course)
                # log.info("notification for course %s",course)
                if redirection_type == "start_date":
                    if course_obj:
                        add_link = (
                            u"{about_base_url}/courses/{course_key}/about".format(
                                about_base_url=configuration_helpers.get_value(
                                    "LMS_ROOT_URL", settings.LMS_ROOT_URL
                                ),
                                course_key=unicode(course.id),
                            )
                        )
                        context = {
                            "course_name": course_obj[0].display_name,
                            "course_number": course_obj[0].number,
                            "add_link": add_link,
                        }
                        subject = course_obj[0].display_name + " Starts Today!"
                        message = render_to_string(
                            "email_template/start_date.html", context
                        )
                if redirection_type == "before_days":
                    if course_obj:
                        course_utc_start = course.start + relativedelta(seconds=1)
                        course_dates = course_utc_start.date()
                        course_utc_time = course_utc_start.time()
                        course_utc_day = course_utc_start.strftime("%a")
                        course_ist_start = now_utc.astimezone(timezone("Asia/Kolkata"))
                        course_ist_date = course_ist_start.date()
                        course_ist_time = course_ist_start.time()
                        context = {
                            "course_name": course_obj[0].display_name,
                            "course_number": course_obj[0].org,
                            "course_dates": course_dates,
                            "course_utc_time": course_utc_time,
                            "course_utc_day": course_utc_day,
                            "course_ist_date": course_ist_date,
                            "course_ist_time": course_ist_time,
                        }
                        subject = course_obj[0].display_name + " Starts Soon!"
                        message = render_to_string(
                            "email_template/before_days.html", context
                        )
                if redirection_type == "course_created":
                    if course_obj:
                        start_date = course_obj[0].start
                        date = start_date.strftime("%m/%d/%Y")
                        course_link = (
                            u"{about_base_url}/courses/{course_key}/about".format(
                                about_base_url=configuration_helpers.get_value(
                                    "LMS_ROOT_URL", settings.LMS_ROOT_URL
                                ),
                                course_key=unicode(course.id),
                            )
                        )
                        context = {
                            "course_name": course_obj[0].display_name,
                            "date": date,
                            "course_link": course_link,
                        }
                        subject = (
                            "Announcing a new event on " + course_obj[0].display_name
                        )
                        message = render_to_string(
                            "email_template/announce_course.html", context
                        )
                if redirection_type == "course_created":
                    course_extra_categoey_id = course_extrainfo.objects.filter(
                        course_id=str(course)
                    )
                    if course_extra_categoey_id:
                        category_id = course_extra_categoey_id[0].category
                        category_specialization_ids = list(
                            categories.objects.filter(id=category_id).values_list(
                                "topic_specialization", flat=True
                            )
                        )
                        if category_specialization_ids:
                            specialization_match_users_list = list(
                                extrafields.objects.filter(
                                    specialization__in=category_specialization_ids
                                ).values_list("user__id", flat=True)
                            )
                            users = User.objects.filter(
                                id__in=specialization_match_users_list
                            )
                        else:
                            users = []
                    else:
                        users = []
                else:
                    enroll = list(
                        CourseEnrollment.objects.filter(
                            course_id=course, is_active=True
                        ).values_list("user_id", flat=True)
                    )
                    users = User.objects.filter(id__in=enroll)
                log.info("users are %s", users)
                if users:
                    users_email_list = list(
                        User.objects.all().values_list("email", flat=True)
                    )
                    from_address = "notifications@docmode.org"
                    send_mail(
                        subject,
                        message,
                        from_address,
                        users_email_list,
                        fail_silently=False,
                    )
                    notifiction_obj_email.status = "sent"
                    notifiction_obj_email.save()
                else:
                    notifiction_obj_email.delete()
        except Exception as e:  # pylint: disable=bare-except
            log.exception("Unable to send Email", exc_info=True)
