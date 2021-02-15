"""
course_discovery  API URLs.
"""

from django.conf import settings
from django.conf.urls import include, url

from openedx.core.djangoapps.wp_course_discovery_api import views

urlpatterns = [
    url(
        r"^api/v1/wp_course/search/discovery/$",
        views.CourseSearchView.as_view(),
        name="wp_course_search_detail",
    ),
    url(
        r"^api/v1/wp_course/search/enrollment/$",
        views.CourseSearchEnrollmentView.as_view(),
        name="wp_course_search_enrollment_detail",
    ),
    url(
        r"^api/v1/wp_course/category/$",
        views.CourseCategoryView.as_view(),
        name="wp_course_category_detail",
    ),
    url(
        r"^api/v1/wp_course/search/discovery_local/$",
        views.CourseSearchView_local.as_view(),
        name="wp_course_search_detail",
    ),
]
