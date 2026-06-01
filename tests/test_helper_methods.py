import unittest

from uptime_kuma_api import MonitorStatus, UptimeKumaException
from uptime_kuma_test_case import UptimeKumaTestCase


class TestHelperMethods(UptimeKumaTestCase):
    def test_monitor_status(self):
        monitor_id = self.add_monitor()
        try:
            status = self.api.get_monitor_status(monitor_id)
            self.assertTrue(type(status) == MonitorStatus)
        except UptimeKumaException as e:
            if "monitor does not exist" not in str(e):
                raise


if __name__ == '__main__':
    unittest.main()
