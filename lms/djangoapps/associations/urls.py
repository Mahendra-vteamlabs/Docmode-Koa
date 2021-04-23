from django.conf import settings
from django.conf.urls import include, url

from lms.djangoapps.associations import views

# from lms.djangoapps.course_api.views import  Wp_CourseDetailView

urlpatterns = [
    url(
        r"^api/v1/in_network_with/$",
        views.in_network_with_api.as_view(),
        name="in_network_with",
    ),
    url(
        r"^api/v1/topic_course_lect_count/$",
        views.topic_course_lect_count_api.as_view(),
        name="topic_course_lect_count",
    ),
    url(r"^api/v1/partners_list/$", views.partners_api.as_view(), name="partners"),
    url(
        r"^api/v1/(?P<association_about>[\w-]+)/$",
        views.partner_details_api.as_view(),
        name="partner_details",
    ),
    url(
        r"^api/v1/assoc_admin/(?P<association_about>[\w-]+)/(?P<emailid>.+)/$",
        views.wp_partner_admin_api.as_view(),
        name="wp_partner_admin",
    ),
    url(r"^api/v1/categories/topics_list/$", views.topics_api.as_view(), name="topics"),
    url(
        r"^api/v1/specializations/specializations_list/$",
        views.specializations_api.as_view(),
        name="specializations",
    ),
    url(
        r"^api/courses/v1/wp_courses/(?P<course_title>[\w-]+)$",
        views.Wp_CourseDetailView.as_view(),
        name="wp_course_detail",
    ),
    url(
        r"^api/v1/home/ongoing_courses/$",
        views.wp_home_ongoing_courses.as_view(),
        name="home_ongoing_courses",
    ),
    url(
        r"^api/v1/home/upcoming_lectures/$",
        views.wp_home_upcoming_lectures.as_view(),
        name="home_upcoming_lectures",
    ),
    url(
        r"^api/v1/users/doctor_lists/$",
        views.doctor_lists.as_view(),
        name="doctor_lists",
    ),
    url(
        r"^api/v1/user_profile/(?P<user_seo_url>[\w-]+)$",
        views.user_profile_api.as_view(),
        name="user_profile_api",
    ),
    url(
        r"^api/v1/doc_and_me_user_profile/(?P<user_id>[\w-]+)$",
        views.doctor_and_me_user_profile_api.as_view(),
        name="doctor_and_me_user_profile_api",
    ),
    url(
        r"^api/v1/sponsored_course_lecture/ad_manager/$",
        views.ad_manager_api.as_view(),
        name="ad_manager_api",
    ),
    url(r"^api/v1/temp/courses/$", views.wp_courses.as_view(), name="wp_courses"),
    url(r"^api/v1/temp/lectures/$", views.wp_lectures.as_view(), name="wp_lectures"),
    url(
        r"^api/v1/temp/reminder_users/$",
        views.reminder_api.as_view(),
        name="wp_reminder",
    ),
    url(
        r"^api/v1/thirdparty/user_registration_api$",
        views.user_registration_api.as_view(),
        name="user_registration_api",
    ),
]
