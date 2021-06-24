import datetime
import logging
import uuid
import warnings
from six.moves.urllib.parse import parse_qs, urlsplit, urlunsplit

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login as django_login
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
from openedx.core.djangoapps.user_authn.cookies import delete_logged_in_cookies, set_logged_in_cookies
from django.contrib.auth.models import User, AnonymousUser
from django.core.validators import ValidationError, validate_email
from django.template.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from django.db import transaction
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from student.tasks import send_activation_email
from student.helpers import (
    AccountValidationError,
    create_or_set_user_attribute_created_on_site,
    generate_activation_email_context,
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
from student.helpers import (
    authenticate_new_user,
    do_create_account,
    custom_do_create_account,
)
from edxmako.shortcuts import render_to_response, render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.utils import generate_password
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import get_template
from lms.djangoapps.specialization.views import specializationName

log = logging.getLogger("edx.student")

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


# @login_required
# @ensure_csrf_cookie
@csrf_exempt
def kol_registration(request):
    data = request.POST.dict()
    log.info("docvidlogin3--> %s", request.__dict__)
    log.info("docvidlogin3--> %s", data)
    http_referer = request.META.get("HTTP_REFERER")
    generated_password = generate_password()
    user = request.user
    if "drlocedev" not in http_referer:
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
                    user, profile, reg = custom_do_create_account(form)
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
        if user.is_authenticated:
            log.info("docvidlogin2--> %s", request.__dict__)
            return redirect(
                "https://docvidya.learn.docmode.org/courses/"
                + data.get("course_id")
                + "/courseware"
            )
        # messages.success(request, 'You are not authorized to view this.')
        else:
            log.info("else-->")
            context = {
                "email": data.get("email"),
                "is_web": data.get("web"),
                "course_id": data.get("course_id"),
                "reg_num": data.get("reg_num"),
                "http_referer": data.get("client_redirect_url"),
            }
            return render_to_response("associations/kol_registration.html", context)


@login_required
@ensure_csrf_cookie
@csrf_exempt
def new_kol_registration(request):

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
                user, profile, reg = custom_do_create_account(form)
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
            return render_to_response("associations/new_kol_registration.html", context)
        else:
            messages.success(request, "Welcome to KOL registration page.")

            context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
            return render_to_response("associations/new_kol_registration.html", context)


def compose_and_send_activation_email(user, profile, user_registration=None):
    """
    Construct all the required params and send the activation email
    through celery task

    Arguments:
        user: current logged-in user
        profile: profile object of the current logged-in user
        user_registration: registration of the current logged-in user
    """
    dest_addr = user.email
    if user_registration is None:
        user_registration = Registration.objects.get(user=user)
    context = generate_activation_email_context(user, user_registration)
    subject = render_to_string("emails/activation_email_subject.txt", context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    message_for_activation = render_to_string("emails/activation_email.txt", context)
    from_address = configuration_helpers.get_value(
        "email_from_address", settings.DEFAULT_FROM_EMAIL
    )
    from_address = configuration_helpers.get_value(
        "ACTIVATION_EMAIL_FROM_ADDRESS", from_address
    )
    if settings.FEATURES.get("REROUTE_ACTIVATION_EMAIL"):
        dest_addr = settings.FEATURES["REROUTE_ACTIVATION_EMAIL"]
        message_for_activation = (
            "Activation for %s (%s): %s\n" % (user, user.email, profile.name)
            + "-" * 80
            + "\n\n"
            + message_for_activation
        )
    send_activation_email.delay(
        subject, message_for_activation, from_address, dest_addr
    )


def viatris_send_activation_email(user, profile, user_registration=None, site=None):
    from django.core.mail import (
        EmailMultiAlternatives,
        get_connection,
        send_mail,
        EmailMessage,
    )

    """
    Construct all the required params and send the activation email
    through celery task

    Arguments:
        user: current logged-in user
        profile: profile object of the current logged-in user
        user_registration: registration of the current logged-in user
    """
    dest_addr = user.email
    if user_registration is None:
        user_registration = Registration.objects.get(user=user)
    context = generate_activation_email_context(user, user_registration)
    context["site"] = site
    log.info("site--> %s,%s", site, context)
    subject = render_to_string("emails/activation_email_subject.txt", context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    # txtmessage_for_activation = render_to_string('emails/activation_email.txt', context)
    htmlmessage_for_activation = get_template("emails/activation_email.html").render(
        context
    )
    from_address = configuration_helpers.get_value(
        "email_from_address", settings.DEFAULT_FROM_EMAIL
    )
    from_address = configuration_helpers.get_value(
        "ACTIVATION_EMAIL_FROM_ADDRESS", from_address
    )
    if settings.FEATURES.get("REROUTE_ACTIVATION_EMAIL"):
        dest_addr = settings.FEATURES["REROUTE_ACTIVATION_EMAIL"]
        htmlmessage_for_activation = (
            "Activation for %s (%s): %s\n" % (user, user.email, profile.name)
            + "-" * 80
            + "\n\n"
            + htmlmessage_for_activation
        )

    msg = EmailMessage(subject, htmlmessage_for_activation, from_address, [dest_addr])
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()


@ensure_csrf_cookie
def custom_registration_form(request):
    generated_password = generate_password()

    mandatory_fields = [
        "username",
        "emailid",
        "password",
        "name",
        "phone",
        "user_type",
        "specialization",
        "hcspecialization",
        "pincode",
        "country",
        "state",
        "city",
        "csrfmiddlewaretoken",
    ]
    extradata = {}
    if request.is_ajax():
        if request.method == "POST":
            vfields = request.POST
            for key in vfields:
                if key not in mandatory_fields:
                    extradata[key] = vfields[key]

            uname = request.POST.get("username", "")
            email = request.POST.get("emailid", "")
            password = request.POST.get("password", generated_password)
            if "fname" and "lname" in request.POST:
                fname = request.POST.get("fname", "")
                lname = request.POST.get("lname", "")
                full_name = fname + " " + lname
            else:
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

            try:
                username_validation = User.objects.get(username=uname)
                if username_validation:
                    date = datetime.datetime.now()
                    curr_time = date.strftime("%f")
                    username = uname + "_" + curr_time

            except ObjectDoesNotExist:
                username = uname

            log.info("username--> %s", username)
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
                log.info("form--> %s", form)
                user, profile, reg = do_create_account(form)
                log.info("username--> %s,%s,%s", user, profile, reg)
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
                return JsonResponse(
                    {
                        "status": "403",
                        "msg": "Account creation not allowed either the username is already taken.",
                    }
                )

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
                user_extra_data=extradata,
                user=user,
            )
            user_extrainfo.save()

            new_user = authenticate_new_user(request, user.username, password)
            django_login(request, new_user)
            request.session.set_expiry(0)
            # log.info(u'details--> %s,%s,%s', user, profile,reg)

            create_comments_service_user(user)

            create_or_set_user_attribute_created_on_site(user, request.site)

            compose_and_send_activation_email(user, profile, reg)
            messages.success(request, "Kol registration successful.")

            response = JsonResponse(
                {
                    "success": True,
                    "redirect_url": "https://mylan.learn.docmode.org/register?next=/oauth2/authorize/confirm",
                }
            )
            return set_logged_in_cookies(request, response, new_user)
    else:
        messages.success(request, "Welcome to KOL registration page.")

        context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
        return render_to_response("associations/custom_registration.html", context)


@ensure_csrf_cookie
def viatris_emas_registration(request):
    generated_password = generate_password()

    mandatory_fields = [
        "username",
        "emailid",
        "password",
        "name",
        "phone",
        "user_type",
        "specialization",
        "hcspecialization",
        "pincode",
        "country",
        "state",
        "city",
        "csrfmiddlewaretoken",
    ]
    extradata = {}
    if request.is_ajax():
        if request.method == "POST":
            vfields = request.POST
            for key in vfields:
                if key not in mandatory_fields:
                    extradata[key] = vfields[key]

            uname = request.POST.get("username", "")
            email = request.POST.get("emailid", "")
            password = request.POST.get("password", generated_password)
            if "fname" and "lname" in request.POST:
                fname = request.POST.get("fname", "")
                lname = request.POST.get("lname", "")
                full_name = fname + " " + lname
            else:
                full_name = request.POST.get("name", "")
            phone = request.POST.get("phone", "")
            user_type = "dr"
            specialization = request.POST.get("specialization", "")
            hcspecialization = request.POST.get("hcspecialization", "")
            pincode = request.POST.get("pincode", "")
            country = request.POST.get("country", "")
            state = request.POST.get("state", "")
            city = request.POST.get("city", "")
            is_active = str2bool(request.POST.get("is_active", True))

            try:
                username_validation = User.objects.get(username=uname)
                if username_validation:
                    date = datetime.datetime.now()
                    curr_time = date.strftime("%f")
                    username = uname + "_" + curr_time

            except ObjectDoesNotExist:
                username = uname

            log.info("username--> %s", username)

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
                return JsonResponse(
                    {
                        "status": "403",
                        "msg": "Account creation not allowed either the username is already taken.",
                    }
                )

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
                user_extra_data=extradata,
                user=user,
            )
            user_extrainfo.save()

            new_user = authenticate_new_user(request, user.username, password)
            django_login(request, new_user)
            request.session.set_expiry(0)
            # log.info(u'details--> %s,%s,%s', user, profile,reg)

            create_comments_service_user(user)

            create_or_set_user_attribute_created_on_site(user, request.site)
            if "viatris" in str(request.site):
                log.info("newmail12%s", request.site)
                viatris_send_activation_email(user, profile, reg, request.site)
            else:
                log.info("oldmail %s", request.site)
                compose_and_send_activation_email(user, profile, reg)
            messages.success(request, "Kol registration successful.")

            response = JsonResponse(
                {
                    "success": True,
                    "userid": user.id,
                    "mobile": phone,
                    "email": email,
                    "name": full_name,
                    "signupdate": datetime.date.today(),
                    "usertype": "dr",
                    "pincode": pincode,
                    "country": country,
                    "redirect_url": "https://mylan.learn.docmode.org/register?next=/oauth2/authorize/confirm",
                }
            )
            return set_logged_in_cookies(request, response, new_user)
    else:
        messages.success(request, "Welcome to KOL registration page.")

        context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
        return render_to_response("associations/custom_registration.html", context)


@ensure_csrf_cookie
def custom_registration_without_zerobounce(request):
    generated_password = generate_password()

    mandatory_fields = [
        "username",
        "emailid",
        "password",
        "name",
        "phone",
        "user_type",
        "specialization",
        "hcspecialization",
        "pincode",
        "country",
        "state",
        "city",
        "csrfmiddlewaretoken",
    ]
    extradata = {}
    if request.is_ajax():
        if request.method == "POST":
            vfields = request.POST
            for key in vfields:
                if key not in mandatory_fields:
                    extradata[key] = vfields[key]

            uname = request.POST.get("username", "")
            email = request.POST.get("emailid", "")
            password = request.POST.get("password", generated_password)
            if "fname" and "lname" in request.POST:
                fname = request.POST.get("fname", "")
                lname = request.POST.get("lname", "")
                full_name = fname + " " + lname
            else:
                full_name = request.POST.get("name", "")
            phone = request.POST.get("phone", "")
            user_type = "dr"
            specialization = request.POST.get("specialization", "")
            hcspecialization = request.POST.get("hcspecialization", "")
            pincode = request.POST.get("pincode", "")
            country = request.POST.get("country", "")
            state = request.POST.get("state", "")
            city = request.POST.get("city", "")
            is_active = str2bool(request.POST.get("is_active", True))

            try:
                username_validation = User.objects.get(username=uname)
                if username_validation:
                    date = datetime.datetime.now()
                    curr_time = date.strftime("%f")
                    username = uname + "_" + curr_time

            except ObjectDoesNotExist:
                username = uname

            log.info("username--> %s", username)

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
                user, profile, reg = custom_do_create_account(form)
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
                return JsonResponse(
                    {
                        "status": "403",
                        "msg": "Account creation not allowed either the username is already taken.",
                    }
                )

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
                user_extra_data=extradata,
                user=user,
            )
            user_extrainfo.save()

            new_user = authenticate_new_user(request, user.username, password)
            django_login(request, new_user)
            request.session.set_expiry(0)
            # log.info(u'details--> %s,%s,%s', user, profile,reg)

            create_comments_service_user(user)

            create_or_set_user_attribute_created_on_site(user, request.site)
            if "viatris" in str(request.site):
                log.info("newmail12%s", request.site)
                viatris_send_activation_email(user, profile, reg, request.site)
            else:
                log.info("oldmail %s", request.site)
                compose_and_send_activation_email(user, profile, reg)
            messages.success(request, "Kol registration successful.")

            response = JsonResponse(
                {
                    "success": True,
                    "userid": user.id,
                    "mobile": phone,
                    "email": email,
                    "name": full_name,
                    "signupdate": datetime.date.today(),
                    "usertype": "dr",
                    "pincode": pincode,
                    "country": country,
                    "redirect_url": "https://mylan.learn.docmode.org/register?next=/oauth2/authorize/confirm",
                }
            )
            return set_logged_in_cookies(request, response, new_user)
    else:
        messages.success(request, "Welcome to KOL registration page.")

        context = {"errors": "welcome", "csrf": csrf(request)["csrf_token"]}
        return render_to_response("associations/custom_registration.html", context)
