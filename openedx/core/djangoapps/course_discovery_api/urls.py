"""
course_discovery  API URLs.
"""

from django.conf import settings
from django.conf.urls import include, url

from openedx.core.djangoapps.course_discovery_api import views

urlpatterns = [
    url(
        r"^api/v1/course/search/discovery/$",
        views.CourseSearchView.as_view(),
        name="course_search_detail",
    ),
    url(
        r"^api/v1/course/search/enrollment/$",
        views.CourseSearchEnrollmentView.as_view(),
        name="course_search_enrollment_detail",
    ),
    url(
        r"^api/v1/course/category/$",
        views.CourseCategoryView.as_view(),
        name="course_category_detail",
    ),
    url(
        r"^api/v1/course/webinarqna/$",
        views.CourseWebinarView.as_view(),
        name="course_webinarqna_detail",
    ),
    url(
        r"^api/v1/user/check/course/webinarqna/$",
        views.CourseCheckcourseWebinarView.as_view(),
        name="user_email_validation_details",
    ),
    url(
        r"^api/v1/user/email_validation/$",
        views.UserEmailValidationView.as_view(),
        name="user_email_validation_details",
    ),
    url(
        r"^api/v1/docmodeprivacy/$",
        views.DocmodePrivacyView.as_view(),
        name="docmode_privacy_detail",
    ),
    url(
        r"^api/v1/docmodetos/$",
        views.DocmodeTosView.as_view(),
        name="docmode_tos_detail",
    ),
    url(
        r"^api/v1/payment/redirect/$",
        views.PaymentRedirect.as_view(),
        name="payment_redirect",
    ),
]
