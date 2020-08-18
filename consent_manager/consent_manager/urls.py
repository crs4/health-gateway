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


from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin

from consent_manager import settings, views
from gui import views as fr_views
from hgw_common.settings import VERSION_REGEX


urlpatterns = [
    path('', fr_views.home),
    path('login/', fr_views.perform_login),
    path('logout/', fr_views.perform_logout),
    path('admin/', admin.site.urls),
    path('saml2/', include('djangosaml2.urls')),
    path('oauth2/', include('oauth2_provider.urls')),
    path('martor/', include('martor.urls')),
    path('protocol/', include('hgw_common.urls')),
    path('confirm_consents/', views.confirm_consent),
    path('{}/consents/abort/'.format(VERSION_REGEX), views.ConsentView.as_view({'post': 'abort'})),
    path('{}/consents/confirm/'.format(VERSION_REGEX), views.ConsentView.as_view({'post': 'confirm'})),
    path('{}/consents/revoke/'.format(VERSION_REGEX), views.ConsentView.as_view({'post': 'revoke_list'}),
        name='consents_revoke'),
    path('{}/consents/find/'.format(VERSION_REGEX), views.ConsentView.as_view({'get': 'find'}),
        name='consents_find'),
    path('{}/consents/'.format(VERSION_REGEX), views.ConsentView.as_view({'get': 'list', 'post': 'create'}),
        name='consents'),
    path('{}/consents/<str:consent_id>/revoke/'.format(VERSION_REGEX), views.ConsentView.as_view({'post': 'revoke'}),
        name='consents_retrieve'),
    path('{}/consents/<str:consent_id>/'.format(VERSION_REGEX),
        views.ConsentView.as_view({'get': 'retrieve', 'put': 'update'}),
        name='consents_retrieve'),
    path('{}/legal-notices/<int:legal_notice_id>'.format(VERSION_REGEX), views.LegalNoticeView
         .as_view({'get': 'get'})),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


