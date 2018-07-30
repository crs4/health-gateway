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


from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework import routers, permissions

from hgw_common.settings import VERSION_REGEX
from hgw_frontend import settings
from .views import view_profile, confirm_request, consents_confirmed, FlowRequestView, Messages

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()


urlpatterns = [
    url(r'^$', view_profile, name='home'),
    url(r'^admin/', admin.site.urls),
    url(r'^saml2/', include('djangosaml2.urls')),
    url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^protocol/', include('hgw_common.urls', namespace='protocol')),
    url(r'^{}/flow_requests/confirm/$'.format(VERSION_REGEX), confirm_request),
    url(r'^{}/flow_requests/consents_confirmed/$'.format(VERSION_REGEX), consents_confirmed),
    url(r'^{}/flow_requests/search/$'.format(VERSION_REGEX), FlowRequestView.as_view({'get': 'search'}),
        name='flow_requests_search'),
    url(r'^{}/flow_requests/$'.format(VERSION_REGEX), FlowRequestView.as_view({'get': 'list', 'post': 'create'}),
        name='flow_requests_list'),
    url(r'^{}/flow_requests/(?P<process_id>\w+)/$'.format(VERSION_REGEX), FlowRequestView.as_view({'get': 'retrieve',
                                                                                                   'delete': 'delete'}),
        name='flow_requests_detail'),
    url(r'^{}/messages/$'.format(VERSION_REGEX), Messages.as_view({'get': 'list'})),
    url(r'^{}/messages/info/$'.format(VERSION_REGEX), Messages.as_view({'get': 'info'})),
    url(r'^{}/messages/(?P<message_id>\d+)/?$'.format(VERSION_REGEX), Messages.as_view({'get': 'retrieve'})),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
