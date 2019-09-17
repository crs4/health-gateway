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


from django.urls import path
from django.contrib import admin
from rest_framework import routers
from django.conf.urls import url, include
from source_endpoint import views
from hgw_common.settings import VERSION_REGEX


router = routers.DefaultRouter()
router.register(r'{}/connectors'.format(VERSION_REGEX), views.ConnectorViewSet)

urlpatterns = [
    path(r'admin/', admin.site.urls),
    path(r'oauth2/', include('oauth2_provider.urls')),
    path(r'', include(router.urls)),
    path(r'api-auth/', include('rest_framework.urls')),
    path(r'protocol/', include('hgw_common.urls')),
]
