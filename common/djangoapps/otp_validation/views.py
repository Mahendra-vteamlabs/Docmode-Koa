import requests
import logging
import json

from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth import authenticate, load_backend, login as django_login, logout
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

logs = logging.getLogger(__name__)


class SendOTP(APIView):
    def post(self, request, *args, **kwargs):
        self.data = request.POST.dict()
        if 'mobile_no' in self.data and self.data.get('mobile_no') != "":
            return self.send_otp_to_mobile()
        elif 'email' in self.data and self.data.get('email') != "":
            return self.send_otp_to_email()
        else:
            return JsonResponse({
                "status": 400,
                "message": "Please enter Valid Mobile Number or Email Address.",
            })

    def send_otp_to_mobile(self):
        mobile = self.data.get('mobile_no')
        try:
            user = User.objects.get(extrafields__phone=mobile)
            if not user.is_active:
                return self.handle_failed_authentication(user)
            otp = OTPManagement.save_otp(user)
            message_template = "Your reset password OTP is: {}".format(otp)
            if not otp:
                return JsonResponse({
                    "status": 400,
                    "message": "Error while sending OTP message"
                })
            send_otp_message_to_user(user, otp)
            return JsonResponse({
                "status": 200,
                "message": "success",
            })
        except Exception as e:
            return JsonResponse({
                "status": 400,
                "message": "Mobile No. does not exists. Try using Email OTP",
                "error": "err2",
            })

    def send_otp_to_email(self):
        email = self.data.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                return self.handle_failed_authentication(user)
            otp = OTPManagement.save_otp(user)
            if not otp:
                return JsonResponse({
                    "status": 400,
                    "message": "Error while sending OTP message"
                })
            else:
                subject = "OTP for login to your Docmode account"
                message = "{} is the OTP for login to Docmode." .format(otp)
                email_from = settings.DEFAULT_FROM_EMAIL
                to = [email]
                resp = send_mail(subject, message, email_from, to)
                return JsonResponse({
                    "status": 200,
                    "message": "success",
                })
        except Exception as e:
            return JsonResponse({
                "status": 400,
                "message": "Email address does not exists.",
                "error": "err1",
            })

    def handle_failed_authentication(self, user):
        compose_and_send_activation_email(user, user.profile)
        return JsonResponse({
            "status": 400,
            "message": "In order to sign in, you need to activate your account. We just sent an activation link to {}.".format(user.email),
        })


class VerifyOTP(APIView):
    def post(self, request, *args, **kwargs):
        data = request.POST.dict()
        otp = data.get('otp')
        mobile_number = data.get('mobile_number')
        email = data.get('email')
        is_web = data.get('web', None)
        if 'mobile_number' in data and data.get('mobile_number') != "":
            verified = OTPManagement.verify_otp(otp, mobile_number)
            user = User.objects.get(extrafields__phone=mobile_number)
        else:
            verified = OTPManagement.verify_otp(otp, email)
            user = User.objects.get(email=email)
        if not verified:
            return Response(data={
                'status': 400,
                'message': _('Invalid OTP'),
                'responseText': _('Invalid OTP')
            }, status=200)
        if is_web is None:
            return Response(data={
                'status': 200,
                'message': 'success',
                'username': user.username,
            }, status=200)

        self.do_login(request, user)
        #django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({
            "status": 200,
            "message": "success",
        })


    def do_login(self, request, user):
        try:
            django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.set_expiry(604800)
            request.user = user
            response = JsonResponse({
                'success': True,
                'redirect_url': "/",
            })
            set_logged_in_cookies(request, response, user)
            logs.debug("Setting user session to never expire")
        except Exception as exc:  # pylint: disable=broad-except
            AUDIT_LOG.critical("Login failed - Could not create session. Is memcached running?")
            logs.critical("Login failed - Could not create session. Is memcached running?")
            logs.exception(exc)



def send_otp_message_to_user(user, otp, message=None, mobile_number=None):
    """
    Sends otp message to user
    """
    url = settings.SMS_URL
    api_key = settings.SMS_API_KEY
    sender_id = settings.SMS_SENDER_ID
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    message = message if message else "{} is the OTP for login to Docmode.".format(otp)

    params = {
        "apikey": api_key,
        "numbers": mobile_number if mobile_number else str(user.extrafields.phone),
        "message": message,
        "sender": sender_id
    }

    try:
        post_request = requests.post(url, data=params)
        logs.info("Response from SMS gateway {}".format(post_request.json()))
        if not post_request.json().get('status') == u'success':
            return {
                "status": post_request.json().get('status'),
                "message": post_request.json().get('message')
            }
        logs.error("OTP message sent successfully to {}".format(user.username))
        return post_request.json()
    except Exception as error:
        logs.error("Error while sending OTP message. The error is {}".format(str(error)))
        return {
            "status": 400,
            "message": "Error while sending OTP message. The error is {}".format(str(error))
        }
