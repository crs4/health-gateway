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
from django.contrib import admin
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from consent_manager import views
from hgw_common.settings import VERSION_REGEX


schema_view = get_schema_view(
   openapi.Info(
      title='Consent Manager API',
      default_version='v1',
      description='REST API of the Consent Manager',
      contact=openapi.Contact(email="vittorio.meloni@crs4.it"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^saml2/', include('djangosaml2.urls')),
    url(r'^swagger(?P<format>.json|.yaml)$', schema_view.without_ui(cache_timeout=None), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=None), name='schema-swagger-ui'),
    url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^protocol/', include('hgw_common.urls', namespace='protocol')),
    url(r'^consents/revoke/$', views.revoke_consents),
    url(r'^{}/consents/confirm/$'.format(VERSION_REGEX), views.confirm_consent),
    url(r'^{}/consents/$'.format(VERSION_REGEX), views.ConsentView.as_view({'get': 'list', 'post': 'create'}),
        name='consents'),
    url(r'^{}/consents/(?P<consent_id>\w+)/$'.format(VERSION_REGEX), views.ConsentView.as_view({'get': 'retrieve'}),
        name='consents'),
]
