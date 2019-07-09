# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from itertools import product

from django.core.exceptions import ImproperlyConfigured
from oauth2_provider.ext.rest_framework import TokenHasScope
from oauth2_provider.ext.rest_framework.permissions import SAFE_HTTP_METHODS
from oauth2_provider.settings import oauth2_settings


class TokenHasResourceDetailedScope(TokenHasScope):
    """
    A different version of TokenHasResourceScope. It allows the View class to specify a custom scope type for
    actions. If it is specified the view will require also the combined scope.
    The view_specific_scopes has this structure

    .. python:

        view_custom_instance = {<action_name>: {'read': <list_of_custom_scopes>, 'write': <list_custom_scopes>}}

    For example: if the View class specifies `required_scopes = ['myscope']` and
    `view_custom_instance = {'myaction': {'read': ['custom']}}`
    the token must have ['myscope:read', 'myscope:custom'] to access the view
    """

    def get_scopes(self, request, view):

        try:
            view_specific_scopes = getattr(view, 'view_specific_scopes')
        except AttributeError:
            view_specific_scopes = {}

        try:
            view_scopes = (
                super(TokenHasResourceDetailedScope, self).get_scopes(request, view)
            )
        except ImproperlyConfigured:
            view_scopes = []

        if request.method.upper() in SAFE_HTTP_METHODS:
            scope_type = [oauth2_settings.READ_SCOPE]
            try:
                if view.action in view_specific_scopes and 'read' in view_specific_scopes[view.action]:
                    scope_type.extend(view_specific_scopes[view.action]['read'])
            except AttributeError:
                pass
        else:
            scope_type = [oauth2_settings.WRITE_SCOPE]
            try:
                if view.action in view_specific_scopes and 'write' in view_specific_scopes[view.action]:
                    scope_type.extend(view_specific_scopes[view.action]['write'])
            except AttributeError:
                pass

        required_scopes = [
            '{0}:{1}'.format(combined_scope[0], combined_scope[1]) for combined_scope in
            product(view_scopes, scope_type)
        ]

        return required_scopes


class IsAuthenticatedOrTokenHasResourceDetailedScope(TokenHasResourceDetailedScope):

    def has_permission(self, request, view):
        # The authenticated user can perform all the actions
        if request.user and not request.user.is_anonymous():
            return request.user.is_authenticated
        else:
            try:
                # Some actions cannot be performed by external clients
                if view.action not in view.oauth_views:
                    return False
                else:
                    # Check the scopes
                    return super(IsAuthenticatedOrTokenHasResourceDetailedScope, self).has_permission(request, view)
            except AttributeError:
                return False
