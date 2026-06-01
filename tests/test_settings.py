import json
import unittest

import uptime_kuma_test_case
from uptime_kuma_test_case import UptimeKumaTestCase


class TestSettings(UptimeKumaTestCase):
    def test_settings(self):
        expected_settings = {
            "checkUpdate": False,
            "checkBeta": False,
            "keepDataPeriodDays": 180,
            "entryPage": "dashboard",
            "searchEngineIndex": False,
            "primaryBaseURL": "",
            "steamAPIKey": "",
            "tlsExpiryNotifyDays": [7, 14, 21],
            "disableAuth": False,
            "trustProxy": False,
            "serverTimezone": "Europe/Berlin",
            "dnsCache": True
        }

        # set settings
        r = self.api.set_settings(self.password, **expected_settings)
        self.assertIn(r["msg"], ["Saved", "Saved."])

        # set settings without password
        r = self.api.set_settings(**expected_settings)
        self.assertIn(r["msg"], ["Saved", "Saved."])

        # get settings
        settings = self.api.get_settings()
        self.compare(settings, expected_settings)

    def test_change_password(self):
        new_password = "321terces"

        # change password
        r = self.api.change_password(self.password, new_password)
        self.assertIn(r["msg"], ["Password has been updated successfully.", "successAuthChangePassword"])

        # check login
        r = self.api.login(self.username, new_password)
        self.assertIn("token", r)

        # restore password
        r = self.api.change_password(new_password, self.password)
        self.assertIn(r["msg"], ["Password has been updated successfully.", "successAuthChangePassword"])

        # refresh global token since password change invalidates the session in v2
        r = self.api.login(self.username, self.password)
        uptime_kuma_test_case.token = r["token"]

    @unittest.skip("uploadBackup socket event removed in Uptime Kuma v2")
    def test_upload_backup(self):
        data = {
            "version": "1.17.1",
            "notificationList": [],
            "monitorList": [],
            "proxyList": []
        }
        data_str = json.dumps(data)
        r = self.api.upload_backup(data_str, "overwrite")
        self.assertIn(r["msg"], ["Backup successfully restored.", "successBackupRestored"])


if __name__ == '__main__':
    unittest.main()
