"""
push notification url API URLs.
"""

from django.conf import settings
from django.conf.urls import include, url

from openedx.core.djangoapps.push_notification import views

urlpatterns = [
    url(
        r"^api/v1/login/mobile/$",
        views.TokenAPIView.as_view(),
        name="user_login_mobile_devise_detail",
    ),
    url(
        r"^api/v1/notification/list/user/$",
        views.ListNotificationViews.as_view(),
        name="user_mobile_notification_detail",
    ),
    url(
        r"^api/v1/custom/login/user/$",
        views.CustomLoginUserViews.as_view(),
        name="delete_access_token_of_user",
    ),
]
