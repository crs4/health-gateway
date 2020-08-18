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

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from martor.widgets import AdminMartorWidget

from consent_manager.models import ConsentManagerUser, ConfirmationCode, Consent, LegalNotice, LegalNoticeVersion


class ConsentManagerUserAdmin(UserAdmin):
    pass


class LegalNoticeAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': AdminMartorWidget},
    }

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if request.method == 'GET':
            obj.new_major = False
            obj.change_comment = ''
        return obj

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        else:
            return ['current_version', 'destination']

    def save_model(self, request, obj, form, change):
        self._bump_version(obj, change)
        super().save_model(request, obj, form, change)

    @staticmethod
    def _bump_version(obj, change):
        """
        :type obj: LegalNotice
        :type change: bool
        """
        from consent_manager.models import LegalNoticeVersion
        new_version = LegalNoticeVersion.objects.create(
            **obj.__args_dict__()
        )
        if not change:
            new_version.v_major = 0
            new_version.v_minor = 0
        else:
            prev_version = obj.current_version
            new_version.v_major = prev_version.v_major
            if obj.new_major:
                new_version.v_major += 1
                new_version.v_minor = 0
            else:
                new_version.v_minor = prev_version.v_minor + 1
        new_version.save()
        obj.current_version = new_version



admin.site.register(ConsentManagerUser, ConsentManagerUserAdmin)
admin.site.register(Consent)
admin.site.register(ConfirmationCode)

admin.site.register(LegalNotice, LegalNoticeAdmin)
admin.site.register(LegalNoticeVersion)
