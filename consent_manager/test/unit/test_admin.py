from django.contrib import admin
from django.test import TestCase

from consent_manager.admin import LegalNoticeAdmin
from consent_manager.models import LegalNotice, LegalNoticeVersion

from mock import patch, MagicMock


class TestAPI(TestCase):
    fixtures = ['test_data.json']

    def test_given_a_legal_notice_when_new_minor_via_admin_then_create_a_new_minor_version(self):
        notice = LegalNotice.objects.get(id=1)
        notice.text += "  *appended*"
        old_version_id = notice.current_version_id
        versions = LegalNoticeVersion.objects.count()
        LegalNoticeAdmin._bump_version(notice, True)
        self.assertEqual(LegalNoticeVersion.objects.count(), versions+1)
        self.assertNotEqual(notice.current_version_id, old_version_id)
        self.assertEqual(LegalNoticeVersion.objects.get(id=old_version_id).v_minor+1,
                         notice.current_version.v_minor)
        self.assertEqual(LegalNoticeVersion.objects.get(id=old_version_id).v_major,
                         notice.current_version.v_major)
        self.assertNotEqual(LegalNoticeVersion.objects.get(id=old_version_id).text,
                            notice.current_version.text)

    def test_given_a_legal_notice_when_new_major_via_admin_then_create_a_new_major_version(self):
        notice = LegalNotice.objects.get(id=1)
        notice.text += "  *appended*"
        old_version_id = notice.current_version_id
        notice.new_major = True
        versions = LegalNoticeVersion.objects.count()
        LegalNoticeAdmin._bump_version(notice, True)
        self.assertEqual(LegalNoticeVersion.objects.count(), versions+1)
        self.assertEqual(LegalNoticeVersion.objects.get(id=old_version_id).v_major+1,
                         notice.current_version.v_major)
        self.assertEqual(notice.current_version.v_minor, 0)

    @staticmethod
    def get_test_legal_notice_with_filled_edit_fields():
        test_legal_notice = LegalNotice.objects.get(id=1)
        test_legal_notice.new_major = True                   # defaults False
        test_legal_notice.change_comment = "Some comment"    # defaults ""
        return test_legal_notice

    def test_given_a_legal_notice_when_saving_then_bump_version_and_save(self):
        test_legal_notice = self.get_test_legal_notice_with_filled_edit_fields()
        with patch.object(admin.ModelAdmin, "save_model", return_value=None) as mock_model_admin, \
            patch.object(LegalNoticeAdmin, "_bump_version", return_value=None) as mock_legal_notice_admin:
            lna = LegalNoticeAdmin(LegalNotice, None)
            lna.save_model(None, test_legal_notice, None, True)
            self.assertEqual(mock_legal_notice_admin.call_count, 1)
            self.assertEqual(mock_model_admin.call_count, 1)

    def test_given_a_legal_notice_when_requesting_for_edit_then_override_comment_and_new_major(self):
        test_legal_notice = self.get_test_legal_notice_with_filled_edit_fields()
        mock_request = MagicMock()
        mock_request.method = 'GET'
        with patch.object(admin.ModelAdmin, "get_object", return_value=test_legal_notice):
            lna = LegalNoticeAdmin(LegalNotice, None)
            legal_notice = lna.get_object(mock_request, 1)
            self.assertEqual(legal_notice.change_comment, '')
            self.assertFalse(legal_notice.new_major)

    def test_given_a_legal_notice_when_submitting_data_then_do_not_override(self):
        test_legal_notice = self.get_test_legal_notice_with_filled_edit_fields()
        mock_request = MagicMock()
        mock_request.method = 'POST'
        with patch.object(admin.ModelAdmin, "get_object", return_value=test_legal_notice):
            lna = LegalNoticeAdmin(LegalNotice, None)
            legal_notice = lna.get_object(mock_request, 1)
            self.assertNotEqual(legal_notice.change_comment, '')
            self.assertTrue(legal_notice.new_major)

    def test_given_user_is_admin_when_requesting_readonly_fields_then_return_empty_list(self):
        mock_request = MagicMock()
        mock_request.user.is_superuser = True

        lna = LegalNoticeAdmin(LegalNotice, None)

        readonly_fields = lna.get_readonly_fields(mock_request)
        self.assertListEqual(readonly_fields, [])

    def test_given_user_is_not_admin_when_requesting_readonly_fields_then_return_current_vers_destination(self):
        mock_request = MagicMock()
        mock_request.user.is_superuser = False

        lna = LegalNoticeAdmin(LegalNotice, None)

        readonly_fields = lna.get_readonly_fields(mock_request)
        self.assertListEqual(readonly_fields, ['current_version', 'destination'])



