import requests
import logging
import json

from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth import (
    authenticate,
    load_backend,
    login as django_login,
    logout,
)
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from common.djangoapps.student.views import compose_and_send_activation_email
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies

from .models import OTPManagement

# get user phone
from lms.djangoapps.reg_form.views import userdetails
from django.shortcuts import redirect
from course_modes.models import CourseMode
from opaque_keys.edx.keys import CourseKey, UsageKey
from student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.reg_form.models import extrafields

logs = logging.getLogger(__name__)


class SendOTP(APIView):
    def post(self, request, *args, **kwargs):
        self.data = request.POST.dict()
        if "mobile_no" in self.data and self.data.get("mobile_no") != "":
            return self.send_otp_to_mobile()
        elif "email" in self.data and self.data.get("email") != "":
            return self.send_otp_to_email()
        else:
            return JsonResponse(
                {
                    "status": 400,
                    "message": "Please enter Valid Mobile Number or Email Address.",
                }
            )

    def send_otp_to_mobile(self):
        mobile = self.data.get("mobile_no")
        try:
            user = User.objects.get(extrafields__phone=mobile)
            if not user.is_active:
                return self.handle_failed_authentication(user)
            otp = OTPManagement.save_otp(user)
            message_template = "Your reset password OTP is: {}".format(otp)
            if not otp:
                return JsonResponse(
                    {"status": 400, "message": "Error while sending OTP message"}
                )
            send_otp_message_to_user(user, otp)
            return JsonResponse(
                {
                    "status": 200,
                    "message": "success",
                }
            )
        except Exception as e:
            return JsonResponse(
                {
                    "status": 400,
                    "message": "Mobile No. does not exists. Try using Email OTP",
                    "error": "err2",
                }
            )

    def send_otp_to_email(self):
        email = self.data.get("email")
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                return self.handle_failed_authentication(user)
            otp = OTPManagement.save_otp(user)
            if not otp:
                return JsonResponse(
                    {"status": 400, "message": "Error while sending OTP message"}
                )
            else:
                subject = "OTP for login to your Docmode account"
                message = "{} is the OTP for login to Docmode.".format(otp)
                email_from = settings.DEFAULT_FROM_EMAIL
                to = [email]
                resp = send_mail(subject, message, email_from, to)
                return JsonResponse(
                    {
                        "status": 200,
                        "message": "success",
                    }
                )
        except Exception as e:
            return JsonResponse(
                {
                    "status": 400,
                    "message": "Email address does not exists.",
                    "error": "err1",
                }
            )

    def handle_failed_authentication(self, user):
        compose_and_send_activation_email(user, user.profile)
        return JsonResponse(
            {
                "status": 400,
                "message": "In order to sign in, you need to activate your account. We just sent an activation link to {}.".format(
                    user.email
                ),
            }
        )


class VerifyOTP(APIView):
    def post(self, request, *args, **kwargs):
        data = request.POST.dict()
        otp = data.get("otp")
        mobile_number = data.get("mobile_number")
        email = data.get("email")
        is_web = data.get("web", None)
        if "mobile_number" in data and data.get("mobile_number") != "":
            verified = OTPManagement.verify_otp(otp, mobile_number)
            user = User.objects.get(extrafields__phone=mobile_number)
        else:
            verified = OTPManagement.verify_otp(otp, email)
            user = User.objects.get(email=email)
        if not verified:
            return Response(
                data={
                    "status": 400,
                    "message": _("Invalid OTP"),
                    "responseText": _("Invalid OTP"),
                },
                status=200,
            )
        if is_web is None:
            return Response(
                data={
                    "status": 200,
                    "message": "success",
                    "username": user.username,
                },
                status=200,
            )

        # self.do_login(request, user)
        # django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # return JsonResponse({
        #     "status": 200,
        #     "message": "success",
        # })

        return do_login(request, user)


def do_login(request, user):
    # _track_user_login(user, request)
    try:
        django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.set_expiry(604800)
        request.user = user
        user_extra_data = userdetails(user.id)
        response = JsonResponse(
            {
                "success": True,
                "redirect_url": request.POST.get("redirect_url", ""),
                "status": 200,
                "email": user.email,
                "phone": user_extra_data.phone,
            }
        )
        logs.info(u"phone--> %s", user_extra_data.phone)
        return set_logged_in_cookies(request, response, user)
        logs.debug("Setting user session to never expire")
    except Exception as exc:  # pylint: disable=broad-except
        AUDIT_LOG.critical(
            "Login failed - Could not create session. Is memcached running?"
        )
        logs.critical("Login failed - Could not create session. Is memcached running?")
        logs.exception(exc)


def send_otp_message_to_user(user, otp, message=None, mobile_number=None):
    """
    Sends otp message to user
    """
    url = settings.SMS_URL
    params = {
        "feedid": settings.SMS_FEEDID,
        "to": mobile_number if mobile_number else str(user.extrafields.phone),
        "text": "OTP is "
        + str(otp)
        + " to validate your login on Docmode.org . This OTP is only valid for 2 mins.",
        "username": settings.SMS_USERNAME,
        "password": settings.SMS_PASSWORD,
        "senderid": settings.SMS_SENDER_ID,
        "templateid": settings.SMS_TEMPLATE_ID,
    }

    try:
        post_request = requests.post(url, data=params)
        logs.info("Response from SMS gateway {}".format(post_request.json()))
        if not post_request.json().get("status") == u"success":
            return {
                "status": post_request.json().get("status"),
                "message": post_request.json().get("message"),
            }
        logs.error("OTP message sent successfully to {}".format(user.username))
        return post_request.json()
    except Exception as error:
        logs.error(
            "Error while sending OTP message. The error is {}".format(str(error))
        )
        return {
            "status": 400,
            "message": "Error while sending OTP message. The error is {}".format(
                str(error)
            ),
        }


###### docvidyalogin api##################
class docvidya(APIView):
    def post(self, request, *args, **kwargs):
        data = request.POST.dict()
        email = data.get("email")
        is_web = data.get("web", None)
        try:
            user_data = User.objects.get(email=email)
            try:
                reg_num = data.get("reg_num", "")
                logs.info("get registration number")
                logs.info("user--> %s", user_data.username)
                user_obj = extrafields.objects.get(user=user_data)
                logs.info("user exist in extrafields")
                if user_obj and reg_num:
                    if user_obj.reg_num != reg_num:
                        user_obj.reg_num = reg_num
                        user_obj.save()
                    else:
                        pass
                else:
                    return Response(
                        data={
                            "status": 404,
                            "message": "Registration number not valid",
                        },
                        status=200,
                    )
                try:
                    course_id = data.get("course_id", "")
                    logs.info("course_id1--> %s", course_id)
                    course_id = course_id.split("+")
                    cnumb = str(course_id[1])
                    courseid = CourseOverview.objects.get(
                        display_number_with_default=cnumb
                    )
                    logs.info("courseid--> %s", courseid)
                    return docvid_login(request, user_data, courseid)

                except:
                    return Response(
                        data={"status": 404, "message": "Invalid Course-Id provided."},
                        status=200,
                    )
            except:
                return Response(
                    data={"status": 404, "message": "Reg num not valid"}, status=200
                )

        except:
            return Response(
                data={"status": 404, "message": "Email does not exist"}, status=200
            )


# class docvidya(APIView):
#    def post(self, request, *args, **kwargs):
#        data = request.POST.dict()
#        email = data.get('email')
#        is_web = data.get('web', None)
#
#        try:
#            user_data = User.objects.get(email=email)
#            course_id = data.get('course_id','')
#            logs.info('course_id1--> %s', course_id)
#            course_id = course_id.split('+')
#            cnumb = str(course_id[1])
#            try:
#                courseid = CourseOverview.objects.get(display_number_with_default=cnumb)
#                logs.info('courseid--> %s', courseid)
#                return docvid_login(request, user_data)
#
#            except:
#               return Response(data={
#                   'status': 404,
#                    'message': 'Invalid Course-Id provided.'
#               }, status=200)

# return redirect('https://docvidya.learn.docmode.org/courses/'+course_id+'/courseware')
#        except:
#           return Response(data={
#                    'status': 404,
#                    'message': 'Email does not exist'
#                }, status=200)


def docvid_login(request, user, courseid):
    # _track_user_login(user, request)
    try:
        django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.set_expiry(604800)
        request.user = user
        user_extra_data = userdetails(user.id)
        course_id = request.POST.get("course_id", "")
        course_id = course_id.replace(" ", "+")
        logs.info("course_id %s", course_id)
        course_key = None
        if course_id:
            course_key = CourseKey.from_string(course_id)
            try:
                check_enrollment = CourseEnrollment.objects.get(
                    user=request.user, course_id=course_key
                )
            except:
                try:
                    course_mode = CourseMode.objects.get(course_id=course_key)
                    CourseEnrollment.enroll(user, course_key, mode=course_mode.mode)
                    logs.info(u"course_mode--> %s", course_mode)
                except:
                    CourseEnrollment.enroll(user, course_key, mode="audit")
        redirect_url = (
            "https://docvidya.learn.docmode.org/courses/" + course_id + "/courseware"
        )
        response = JsonResponse(
            {
                "success": True,
                "redirect_url": redirect_url,
                "status": 200,
                "email": user.email,
            }
        )
        return set_logged_in_cookies(request, response, user)
        logs.debug("Setting user session to never expire")
    except Exception as exc:  # pylint: disable=broad-except
        # AUDIT_LOG.critical("Login failed - Could not create session. Is memcached running?")
        logs.critical("Login failed - Could not create session. Is memcached running?")
        logs.exception(exc)
