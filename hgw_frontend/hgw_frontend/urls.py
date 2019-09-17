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


from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework import routers

from hgw_common.settings import VERSION_REGEX
from hgw_frontend import settings
from hgw_frontend.views import Profiles
from .views import confirm_request, consents_confirmed, FlowRequestView, Messages, Sources, ChannelView

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()

app_name = 'hgw_frontend'
urlpatterns = [
    path(r'', admin.site.urls),
    path(r'saml2/', include('djangosaml2.urls')),
    path(r'oauth2/', include('oauth2_provider.urls')),
    path(r'protocol/', include('hgw_common.urls')),
    path(r'{}/flow_requests/confirm/'.format(VERSION_REGEX), confirm_request),
    path(r'{}/flow_requests/consents_confirmed/'.format(VERSION_REGEX), consents_confirmed),
    path(r'{}/flow_requests/search/'.format(VERSION_REGEX), FlowRequestView.as_view({'get': 'search'}),
        name='flow_requests_search'),
    path(r'{}/flow_requests/'.format(VERSION_REGEX), FlowRequestView.as_view({'get': 'list', 'post': 'create'}),
        name='flow_requests_list'),
    path(r'{}/flow_requests/<str:process_id>/'.format(VERSION_REGEX), FlowRequestView.as_view({'get': 'retrieve',
                                                                                                   'delete': 'delete'}),
        name='flow_requests_detail'),
    path(r'{}/flow_requests/<str:process_id>/channels/'.format(VERSION_REGEX), 
        FlowRequestView.as_view({'get': 'channels'}),
        name='flow_requests_channels'),
    path(r'{}/channels/search/'.format(VERSION_REGEX), ChannelView.as_view({'get': 'search'})),
    path(r'{}/channels/'.format(VERSION_REGEX), ChannelView.as_view({'get': 'list'})),
    path(r'{}/channels/<str:channel_id>/'.format(VERSION_REGEX), ChannelView.as_view({'get': 'retrieve'})),
    path(r'{}/messages/'.format(VERSION_REGEX), Messages.as_view({'get': 'list'})),
    path(r'{}/messages/info/'.format(VERSION_REGEX), Messages.as_view({'get': 'info'})),
    path(r'{}/messages/<int:message_id>/'.format(VERSION_REGEX), Messages.as_view({'get': 'retrieve'})),
    path(r'{}/sources/'.format(VERSION_REGEX), Sources.as_view({'get': 'list'})),
    path(r'{}/sources/<str:source_id>/'.format(VERSION_REGEX), Sources.as_view({'get': 'retrieve'})),
    path(r'{}/profiles/'.format(VERSION_REGEX), Profiles.as_view({'get': 'list'})),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
