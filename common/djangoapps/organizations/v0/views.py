# pylint: disable=too-many-ancestors
"""
Views for organizations end points.
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from openedx.core.lib.api.authentication import OAuth2Authentication

from common.djangoapps.organizations.models import Organization
from common.djangoapps.organizations.serializers import OrganizationSerializer


class OrganizationsViewSet(viewsets.ReadOnlyModelViewSet):
    """Organization view to fetch list organization data or single organization
    using organization short name.
    """

    queryset = Organization.objects.filter(active=True)  # pylint: disable=no-member
    serializer_class = OrganizationSerializer
    lookup_field = "short_name"
    authentication_classes = (
        OAuth2Authentication,
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (IsAuthenticated,)
