from . import views
from django.conf.urls import include, url
from django.conf import settings
from .views import get_credit_points


urlpatterns = [
    url(
        r"^course_about/{}$".format(settings.COURSE_KEY_PATTERN),
        get_credit_points,
        name="get_credit_points",
    ),
]
