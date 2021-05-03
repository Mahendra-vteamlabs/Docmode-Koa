"""
URLS for organizations
"""
from django.conf.urls import url, include

app_name = "common.djangoapps.organizations"  # pylint: disable=invalid-name
urlpatterns = [
    url(r"^v0/", include("common.djangoapps.organizations.v0.urls")),
]
