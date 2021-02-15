import json
import logging
import urlparse
import urllib
from datetime import datetime

import pytz
import string
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, reverse
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django_countries import countries
from django.core.exceptions import ObjectDoesNotExist
import third_party_auth
from lms.djangoapps.commerce.models import CommerceConfiguration
from edxmako.shortcuts import render_to_response, render_to_string
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from .models import (
    Sponsored_course_users,
    associations_ad_manager,
    user_view_counter,
    disclaimer_agreement_status,
)
from openedx.core.lib.edx_api_utils import get_edx_api_data

AUDIT_LOG = logging.getLogger("audit")
log = logging.getLogger(__name__)
User = get_user_model()  # pylint:disable=invalid-name
# Create your views here.


def sponsored_user(user, course_id):
    """Given a user, get the detail of all the orders from the Ecommerce service.

    Args:
        user (User): The user to authenticate as when requesting ecommerce.

    Returns:
        list of dict, representing orders returned by the Ecommerce service.
    """
    no_data = []
    commerce_configuration = CommerceConfiguration.current()
    user_query = {"username": user.username}

    use_cache = commerce_configuration.is_cache_enabled
    cache_key = (
        commerce_configuration.CACHE_KEY + "." + str(user.id) if use_cache else None
    )
    api = ecommerce_api_client(user)
    commerce_user_orders = get_edx_api_data(
        commerce_configuration,
        "orders",
        api=api,
        querystring=user_query,
        cache_key=cache_key,
    )
    user_order = "N/A"
    # log.info('======data %s', commerce_user_orders)
    if commerce_user_orders:
        if not user.is_staff:
            for order in commerce_user_orders:
                order_course_id = order["lines"][0]["product"]["attribute_values"][1][
                    "value"
                ]
                if not order["vouchers"]:
                    order_coupon_code = "nocode"
                else:
                    order_coupon_code = order["vouchers"][0]["code"]
                    # log.info('======coupon_code %s', order_coupon_code)
                try:
                    Sponsored_course = Sponsored_course_users.objects.get(
                        course_id=course_id, coupon_code__contains=order_coupon_code
                    )
                    user_order = Sponsored_course.video_url
                    log.info("sponsored_data---> %s", user_order)
                    log.info("user--> %s", user)
                    # log.info('======coupon_code %s', order_coupon_code)
                    # log.info('======user_order %s', user_order)
                except ObjectDoesNotExist:
                    user_order = "n/a"
                    # log.info('======user_order %s', user_order)

                return user_order


def get_association_ad_data(courseid):
    assoc_data = "n/a"
    try:
        ad_data = associations_ad_manager.objects.get(course_id=courseid)
        if ad_data.video_url:
            assoc_data = ad_data.video_url
    except ObjectDoesNotExist:
        assoc_data = "n/a"

    return assoc_data


def user_ad_view_counter(userid, courseid):
    try:
        ad_result = user_view_counter.objects.get(user_id=userid, course_id=courseid)
        view_counter = ad_result.mcounter
    except ObjectDoesNotExist:
        view_counter = 0

    return view_counter


def disclaimer_view(courseid):
    dsclmr = "n/a"
    try:
        disclaimer = associations_ad_manager.objects.get(course_id=courseid)
        if disclaimer.disclaimer:
            dsclmr = disclaimer.disclaimer
    except ObjectDoesNotExist:
        dsclmr = "n/a"
    return dsclmr


def disclaimer_status(userid, courseid):
    dsclmr = "n/a"
    try:
        disclaimer = disclaimer_agreement_status.objects.get(
            user_id=userid, course_id=courseid
        )
        if disclaimer.status:
            dsclmr = disclaimer.status
    except ObjectDoesNotExist:
        dsclmr = "n/a"
    return dsclmr
