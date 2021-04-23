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
        from lms.djangoapps.course_extrainfo.models import course_extrainfo
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
        
        coursetype = course_extrainfo.objects.filter(course_type=1)
        association_list = []
        for courseid in coursetype:
            course_id = CourseKey.from_string(courseid.course_id)
            enrolled_users_lists = CourseEnrollment.objects.filter(course_id=course_id)
            for userid in enrolled_users_lists:
                try:
                    non_passed_users = PersistentCourseGrade.objects.get(user_id=userid.user_id,course_id=userid.course_id,letter_grade='')
                    user_lastlogin = User.objects.get(id=non_passed_users.user_id)
                    if user_lastlogin.last_login is not None :
                        diffdate = datetime.datetime.now(UTC) - user_lastlogin.last_login
                        association_dict = {}
                        if diffdate.days >= 3:
                            try:
                                course_email = Custom_email.objects.get(course_id=userid.course_id,template_name='universal_reminder_email.template')
                                if course_email:
                                    log.info('course_email %s',course_email)
                                    cid1 = str(course_id)
                                    userprofile = getuserfullprofile(user_lastlogin.id)
                                    connection = get_connection()
                                    connection.open()
                                    email = user_lastlogin.email
                                    
                                    message = 'Congratulations' + user_lastlogin.username + 'you are enrolled in the course'

                                    from_addr = "notifications@docmode.org"
                                    course = get_course(course_id)
                                    global_email_context = _get_course_email_context(course)

                                    email_context = {'name': '', 'email': ''}
                                    email_context.update(global_email_context)
                                    email_context['email'] = email
                                    email_context['name'] = userprofile.name
                                    email_context['user_id'] = user_lastlogin.id
                                    email_context['course_id'] = course_id
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
                                    mail_to_users = custom_mail_to_users(course_emailid=course_email.id,user_id=user_lastlogin.id,user_email=email,course_id=course_id)
                                    mail_to_users.save()
                                    log.info(u'email_msg2->%s', email_msg)
                            except ObjectDoesNotExist:
                                cid = CourseKey.from_string('course-v1:docmode+DM001+2018_Feb_DM001')
                                course_email = Custom_email.objects.get(course_id=cid,template_name='universal_reminder_email.template')
                                if course_email:
                                    log.info('course_email %s',course_email)
                                    cid1 = str(course_id)
                                    userprofile = getuserfullprofile(user_lastlogin.id)
                                    connection = get_connection()
                                    connection.open()
                                    email = user_lastlogin.email
                                    
                                    message = 'Congratulations' + user_lastlogin.username + 'you are enrolled in the course'

                                    from_addr = "notifications@docmode.org"
                                    course = get_course(course_id)
                                    global_email_context = _get_course_email_context(course)

                                    email_context = {'name': '', 'email': ''}
                                    email_context.update(global_email_context)
                                    email_context['email'] = email
                                    email_context['name'] = userprofile.name
                                    email_context['user_id'] = user_lastlogin.id
                                    email_context['course_id'] = course_id
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
                                    mail_to_users = custom_mail_to_users(course_emailid=course_email.id,user_id=user_lastlogin.id,user_email=email,course_id=course_id)
                                    mail_to_users.save()
                                    log.info(u'email_msg2->%s', email_msg)
                except ObjectDoesNotExist:
                    non_passed_users = "n/a"