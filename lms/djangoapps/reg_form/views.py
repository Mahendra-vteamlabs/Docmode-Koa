import datetime
import logging
import uuid
import warnings
from six.moves.urllib.parse import parse_qs, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import redirect, render
from .models import extrafields, medical_councils
from django.core.exceptions import ObjectDoesNotExist
from student.models import UserProfile
from django.contrib.auth.models import User, AnonymousUser
from django.core.validators import ValidationError, validate_email
from django.template.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from django.db import transaction
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from student.helpers import (
    AccountValidationError,
    create_or_set_user_attribute_created_on_site
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

# Create your views here.
def ajaxform(request):
    if request.method == "POST":

        usertype = request.POST["usertype"]

        return HttpResponse("registration/reg_usertype.html", {"usertype": usertype})


def userdetails(userid):
    try:
        getDetails = extrafields.objects.get(user_id=userid)
    except ObjectDoesNotExist:
        getDetails = None

    return getDetails


def getuserfullprofile(userid):
    try:
        getDetails = UserProfile.objects.get(user_id=userid)
    except ObjectDoesNotExist:
        getDetails = None

    return getDetails


def get_authuser(userid):
    try:
        getDetails = User.objects.get(id=userid)
    except ObjectDoesNotExist:
        getDetails = None

    return getDetails


def medical_council_lists():
    mci_list = medical_councils.objects.all()
    return mci_list


def str2bool(s):
    s = str(s)
    return s.lower() in ("yes", "true", "t", "1")


@login_required
@ensure_csrf_cookie
def kol_registration(request):
    generated_password = generate_password()
    user = request.user
    if user.is_staff:
        if request.method == "POST":
            username = request.POST.get("username", "")
            email = request.POST.get("emailid", "")
            password = request.POST.get("password", generated_password)
            full_name = request.POST.get("name", "")
            phone = request.POST.get("phone", "")
            user_type = request.POST.get("user_type", "")
            specialization = request.POST.get("specialization", "")
            hcspecialization = request.POST.get("hcspecialization", "")
            pincode = request.POST.get("pincode", "")
            country = request.POST.get("country", "")
            state = request.POST.get("state", "")
            city = request.POST.get("city", "")
            is_active = str2bool(request.POST.get("is_active", True))

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
                specialization_id=specialization,
                hcspecialization_id=hcspecialization,
                user=user,
            )
            user_extrainfo.save()
            create_comments_service_user(user)

            create_or_set_user_attribute_created_on_site(user, request.site)
            messages.success(request, "Kol registration successful.")
            context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
            return render_to_response("associations/kol_registration.html", context)
        else:
            messages.success(request, "Welcome to KOL registration page.")

            context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
            return render_to_response("associations/kol_registration.html", context)
    else:
        messages.success(request, "You are not authorized to view this.")

        context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
        return render_to_response("associations/kol_registration.html", context)
