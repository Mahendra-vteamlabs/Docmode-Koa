"""
Views that dispatch processing of OAuth requests to django-oauth2-provider or
django-oauth-toolkit as appropriate.
"""


import json
import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import HttpResponse
from edx_django_utils import monitoring as monitoring_utils
from oauth2_provider import views as dot_views
from ratelimit import ALL
from ratelimit.decorators import ratelimit
from oauth2_provider.models import AccessToken

from openedx.core.djangoapps.auth_exchange import views as auth_exchange_views
from openedx.core.djangoapps.oauth_dispatch import adapters
from openedx.core.djangoapps.oauth_dispatch.dot_overrides import views as dot_overrides_views
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_from_token

log = logging.getLogger(__name__)

class _DispatchingView(View):
    """
    Base class that route views to the appropriate provider view.  The default
    behavior routes based on client_id, but this can be overridden by redefining
    `select_backend()` if particular views need different behavior.
    """

    dot_adapter = adapters.DOTAdapter()

    def get_adapter(self, request):
        """
        Returns the appropriate adapter based on the OAuth client linked to the request.
        """
        client_id = self._get_client_id(request)
        monitoring_utils.set_custom_attribute('oauth_client_id', client_id)

        return self.dot_adapter

    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch the request to the selected backend's view.
        """
        backend = self.select_backend(request)
        view = self.get_view_for_backend(backend)
        return view(request, *args, **kwargs)

    def select_backend(self, request):
        """
        Given a request that specifies an oauth `client_id`, return the adapter
        for the appropriate OAuth handling library.  If the client_id is found
        in a django-oauth-toolkit (DOT) Application, use the DOT adapter,
        otherwise use the django-oauth2-provider (DOP) adapter, and allow the
        calls to fail normally if the client does not exist.
        """
        return self.get_adapter(request).backend

    def get_view_for_backend(self, backend):
        """
        Return the appropriate view from the requested backend.
        """
        if backend == self.dot_adapter.backend:
            return self.dot_view.as_view()
        else:
            raise KeyError(
                'Failed to dispatch view. Invalid backend {}'.format(backend))

    def _get_client_id(self, request):
        """
        Return the client_id from the provided request
        """
        if request.method == u'GET':
            return request.GET.get('client_id')
        else:
            return request.POST.get('client_id')


@method_decorator(
    ratelimit(
        key='openedx.core.djangoapps.util.ratelimit.real_ip', rate=settings.RATELIMIT_RATE,
        method=ALL, block=True
    ), name='dispatch'
)
class AccessTokenView(_DispatchingView):
    """
    Handle access token requests.
    """
    dot_view = dot_views.TokenView

    def dispatch(self, request, *args, **kwargs):
        response = super(AccessTokenView, self).dispatch(
            request, *args, **kwargs)

        token_type = request.POST.get('token_type',
                                      request.META.get('HTTP_X_TOKEN_TYPE', 'no_token_type_supplied')).lower()
        monitoring_utils.set_custom_attribute('oauth_token_type', token_type)
        monitoring_utils.set_custom_attribute(
            'oauth_grant_type', request.POST.get('grant_type', ''))

        if response.status_code == 200 and token_type == 'jwt':
            response.content = self._build_jwt_response_from_access_token_response(
                request, response)

        return response

    def _build_jwt_response_from_access_token_response(self, request, response):
        """ Builds the content of the response, including the JWT token. """
        token_dict = json.loads(response.content.decode('utf-8'))
        jwt = create_jwt_from_token(token_dict, self.get_adapter(request))
        token_dict.update({
            'access_token': jwt,
            'token_type': 'JWT',
        })
        return json.dumps(token_dict)


class AuthorizationView(_DispatchingView):
    """
    Part of the authorization flow.
    """
    dot_view = dot_overrides_views.EdxOAuth2AuthorizationView


class AccessTokenExchangeView(_DispatchingView):
    """
    Exchange a third party auth token.
    """
    dot_view = auth_exchange_views.DOTAccessTokenExchangeView


class RevokeTokenView(_DispatchingView):
    """
    Dispatch to the RevokeTokenView of django-oauth-toolkit
    """
    dot_view = dot_views.RevokeTokenView


class UserInfoView(View):
    """
    Implementation of the Basic OpenID Connect UserInfo endpoint as described in:

    - http://openid.net/specs/openid-connect-basic-1_0.html#UserInfo

    By default it returns all the claims available to the `access_token` used, and available
    to the claim handlers configured by `OAUTH_OIDC_USERINFO_HANDLERS`

    In addition to the standard UserInfo response, this view also accepts custom scope
    and claims requests, using the scope and claims parameters as described in:

    http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Normally, such requests can only be done when requesting an ID Token. However, it is
    also convinient to support then in the UserInfo endpoint to do simply authorization checks.

    It ignores the top level claims request for `id_token`, in the claims
    request, using only the `userinfo` section.

    All requests to this endpoint must include at least the 'openid' scope.

    Currently only supports GET request, and does not sign any responses.

    """

    def get(self, request, *_args, **_kwargs):
        """
        Respond to a UserInfo request.

        Two optional query parameters are accepted, scope and claims.
        See the references above for more details.

        """
        # Get the header value
        token = request.META.get('HTTP_AUTHORIZATION', '')
        # Trim the Bearer portion
        token = token.replace('Bearer ', '')
        log.info("AccessToken: {}".format(token))
        if token:
            # Verify token exists and is valid
            access_token = AccessToken.objects.filter(token=token)
            if access_token:
                access_token = access_token[0]
            else:
                access_token = None

            if access_token is None:
                error_msg = 'invalid_token'
            else:
                user = access_token.user
        else:
            # Return an error response if no token supplied
            error_msg = 'access_denied'

        try:
            profile_name = ""
            if hasattr(user, "profile"):
                profile_name = user.profile.name
            userinfo = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.get_full_name() or profile_name
            }
            return JsonResponse(userinfo, status=200)
        except ValueError as exception:
            log.info("Error during user profile. Error: {}".format(str(exception)))
            return self._bad_request(str(exception))

    def _bad_request(self, msg):
        """ Return a 400 error with JSON content. """
        return JsonResponse({'error': msg}, status=400)


class JsonResponse(HttpResponse):
    """ Simple JSON Response wrapper. """

    def __init__(self, content, status=None, content_type='application/json'):
        super(JsonResponse, self).__init__(
            content=json.dumps(content),
            status=status,
            content_type=content_type,
        )
