"""
Command to delete all rows from the api_admin_historicalapiaccessrequest table.
"""
import datetime
import logging
from pytz import UTC
from django.core.management.base import BaseCommand


log = logging.getLogger('reminder_email')

class Command(BaseCommand):


    def handle(self, *args, **kwargs):
        from student.models import User
        from lms.djangoapps.reg_form.views import get_authuser
        from student.models import CourseEnrollment
        from lms.djangoapps.grades.models import PersistentCourseGrade
        from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
        from lms.djangoapps.send_custom_email.models import Custom_email, CustomEmailTemplate, custom_mail_to_users
        from django.core.mail import EmailMultiAlternatives, get_connection
        from opaque_keys.edx.keys import CourseKey, UsageKey
        from django.core.exceptions import ObjectDoesNotExist
        from lms.djangoapps.reg_form.views import getuserfullprofile, userdetails
        from bulk_email.tasks import _get_course_email_context
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
        
        cid = CourseKey.from_string('course-v1:CIMS+CIMS002+2020_May_CIMS002')
        # enrolled user'slist in dasil course
        enroll_user_list = CourseEnrollment.objects.filter(course_id=cid)
        enroll_userid = []
        for userid in enroll_user_list:
            user_id = userid.user_id
            enroll_userid.append(user_id)
        
        # dasil users who has not passed the course
        non_passed_users = PersistentCourseGrade.objects.filter(user_id__in=enroll_userid,course_id=cid,letter_grade='')
        nonpassed_userids = []
        for userid in non_passed_users:
            user_id = userid.user_id
            nonpassed_userids.append(user_id)

        # users list to get user emailid
        user_lastlogin = User.objects.filter(email='dev.singh1991@outlook.com')
        association_list = []
        for user in user_lastlogin:
            if user_lastlogin is not None:
                enrolldate = CourseEnrollment.objects.get(course_id=cid, user_id=user.id)
                diffdate = datetime.datetime.now(UTC) - user.last_login
                association_dict = {}

                if diffdate.days >= 3:
                    try:
                        course_email = Custom_email.objects.get(course_id=cid,template_name='reminder_email.template')
                        if course_email:
                            cid1 = str(course_email.course_id)
                            userprofile = getuserfullprofile(user.id)
                            connection = get_connection()
                            connection.open()
                            email = user.email
                            
                            message = 'Congratulations' + user.username + 'you are enrolled in the course'

                            from_addr = "notifications@docmode.org"
                            course = get_course(cid)
                            global_email_context = _get_course_email_context(course)

                            email_context = {'name': '', 'email': ''}
                            email_context.update(global_email_context)
                            email_context['email'] = email
                            email_context['name'] = userprofile.name
                            email_context['user_id'] = user.id
                            email_context['course_id'] = cid
                            email_context['login_url'] = "http://cims.docmode.org/login?next="+cid
                            subject = "Keep learning in " + email_context['course_title']
                            email_template = course_email.get_template()
                            plaintext_msg = email_template.render_plaintext(course_email.text_message, email_context)
                            html_msg = email_template.render_htmltext(course_email.html_message, email_context)

                            email_msg = EmailMultiAlternatives(
                                subject,
                                plaintext_msg,
                                from_addr,
                                [email],
                                connection=connection
                            )
                            
                            email_msg.attach_alternative(html_msg, 'text/html')
                            email_msg.send()
                            mail_to_users = custom_mail_to_users(course_emailid=course_email.id,user_id=user.id,user_email=email,course_id=cid)
                            mail_to_users.save()
                            log.info(u'email_msg2->%s', email_msg)
                    except ObjectDoesNotExist:
                        course_email = "N/a"