"""
Command to delete all rows from the api_admin_historicalapiaccessrequest table.
"""
import datetime
import logging

from django.core.management.base import BaseCommand


log = logging.getLogger("my_schedule_job")


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        from dateutil.relativedelta import relativedelta
        from django.db.models import Q
        from openedx.core.djangoapps.push_notification.tasks import (
            send_new_message_notification,
        )
        from openedx.core.djangoapps.push_notification.models import (
            DocmodeNotification,
            DocmodeNotificationCourse,
            MobileDiviseDetail,
        )
        from openedx.core.djangoapps.content.course_overviews.models import (
            CourseOverview,
        )

        log.info("cron job called")
        current_date = datetime.datetime.today().date()
        current_datetime = datetime.datetime.today().replace(microsecond=0)
        courses = CourseOverview.objects.filter(Q(start__gte=current_date))

        course_start_list = []
        course_start_hours_list = []
        course_created_list = []
        log.info("courses list done")
        for course in courses:
            course_start = course.start + relativedelta(seconds=1)
            course_create = course.created + relativedelta(seconds=1)
            course_create_date = course_create
            course_start = course_start.replace(tzinfo=None)
            notification_start_datetime = course_start - relativedelta(days=3)
            notification_start_date = notification_start_datetime.date()
            notification_start_hours = course_start - relativedelta(hours=3)
            notification_start_hours_date = notification_start_hours.today()
            log.info("checking time comparision for notification ")
            log.info("stattime %s", notification_start_datetime)
            log.info("stattime %s", current_datetime)
            if (
                current_date == course_start.date()
                and current_datetime <= notification_start_hours_date
            ):
                sent_notification_course = DocmodeNotificationCourse.objects.filter(
                    course_id=course.id, status="sent", redirection_type="start_date"
                )
                log.info("start_date notifiocation course found")
                if not sent_notification_course:
                    course_start_list.append(str(course.id))
            if current_date == notification_start_date:
                sent_notification_course = DocmodeNotificationCourse.objects.filter(
                    course_id=course.id, status="sent", redirection_type="before_days"
                )
                if not sent_notification_course:
                    course_start_hours_list.append(str(course.id))
            if current_date == course_create_date:
                sent_notification_course = DocmodeNotificationCourse.objects.filter(
                    course_id=course.id,
                    status="sent",
                    redirection_type="course_created",
                )
                if not sent_notification_course:
                    course_created_list.append(str(course.id))
        log.info("get all course list of notification send")
        values = []
        value = {}
        value["course_id"] = course_start_list
        value["redirection_type"] = "start_date"
        values.append(value)
        value = {}
        value["course_id"] = course_start_hours_list
        value["redirection_type"] = "before_days"
        values.append(value)
        value = {}
        value["course_id"] = course_created_list
        value["redirection_type"] = "course_created"
        values.append(value)
        log.info("send notification task for %s", values)
        send_new_message_notification.delay(values=values)
