from django.conf import settings
from django.conf.urls import url
from .views import (
    get_program_details,
    ProgramCustomList,
    ProgramCustomDetail,
    Custom_program_payment,
    ProgramCuponCheck,
    ProgramCuponRemove,
)

urlpatterns = [
    url(
        r"^program/(?P<program_id>\d+)/details$",
        get_program_details,
        name="get_program_details",
    ),
    url(
        r"^api/v1/wp_course/programlist/$",
        ProgramCustomList.as_view(),
        name="wp_customprogram_list",
    ),
    url(
        r"^api/v1/wp_course/programdetail/$",
        ProgramCustomDetail.as_view(),
        name="wp_customprogram_detail",
    ),
    url(
        r"^api/v1/wp_course/custom_program_payment/$",
        Custom_program_payment.as_view(),
        name="custom_program_payment",
    ),
    url(
        r"^api/v1/wp_course/program_coupon/$",
        ProgramCuponCheck.as_view(),
        name="program_coupon",
    ),
    url(
        r"^api/v1/wp_course/program_coupon_remove/$",
        ProgramCuponRemove.as_view(),
        name="program_coupon_remove",
    ),
]
