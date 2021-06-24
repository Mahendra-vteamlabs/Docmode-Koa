"""
URLs for otp validation app
"""

from django.conf import settings
from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r"^api/mobile/request/otp/$",
        views.SendOTP.as_view(),
        name="send_otp",
    ),
    url(r"^api/mobile/verify/otp/$", views.VerifyOTP.as_view(), name="verify_otp"),
    url(
        r"^api/doc_vidya/user_authentication/$",
        views.docvidya_authentication.as_view(),
        name="docvidya_authentication",
    ),
    url(r"^api/doc_vidya/login/$", views.docvidya.as_view(), name="docvidya"),
    url(r"^doc_login/$", views.doc_login, name="doc_login"),
]
