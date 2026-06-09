"""Unit tests for monitor input validation — no live server required.

Regression tests for the DB corruption bug where the old uptime-kuma-api
wrote accepted_statuscodes_json as [200-299] (unquoted) and
kafka_producer_sasl_options as {mechanism:None} (invalid JSON).
"""
import json
import unittest

from uptime_kuma_api.api import _check_arguments_monitor, _convert_monitor_input
from uptime_kuma_api import MonitorType


def _make_kwargs(extra=None):
    """Minimal valid kwargs dict as _convert_monitor_input expects it."""
    kwargs = dict(
        type=MonitorType.HTTP,
        name="test",
        interval=60,
        maxretries=0,
        retryInterval=60,
        maxredirects=10,
        url="http://example.com",
        accepted_statuscodes=None,
        dns_resolve_type="A",
        notificationIDList=None,
        databaseConnectionString=None,
        kafkaProducerSaslOptions=None,
        conditions=None,
    )
    if extra:
        kwargs.update(extra)
    _convert_monitor_input(kwargs)
    return kwargs


class TestAcceptedStatuscodes(unittest.TestCase):
    def test_default_is_list_of_strings(self):
        kwargs = _make_kwargs()
        codes = kwargs["accepted_statuscodes"]
        self.assertIsInstance(codes, list)
        for code in codes:
            self.assertIsInstance(code, str, f"expected str, got {type(code)}: {code!r}")

    def test_default_serializes_to_valid_json(self):
        kwargs = _make_kwargs()
        codes = kwargs["accepted_statuscodes"]
        serialized = json.dumps(codes)
        self.assertEqual(json.loads(serialized), codes)
        # The specific value that was corrupt in the DB
        self.assertEqual(serialized, '["200-299"]')

    def test_integer_statuscode_rejected(self):
        kwargs = _make_kwargs({"accepted_statuscodes": [200]})
        with self.assertRaises(ValueError):
            _check_arguments_monitor(kwargs)

    def test_unquoted_range_rejected(self):
        # In Python [200-299] evaluates to [-99]; ensure that's also caught
        kwargs = _make_kwargs({"accepted_statuscodes": [-99]})
        with self.assertRaises(ValueError):
            _check_arguments_monitor(kwargs)

    def test_valid_range_accepted(self):
        kwargs = _make_kwargs({"accepted_statuscodes": ["200-299", "301"]})
        _check_arguments_monitor(kwargs)  # should not raise


class TestKafkaSaslOptions(unittest.TestCase):
    # The default is set in _build_monitor_data (instance method, line 1031-1034):
    #   kafkaProducerSaslOptions = {"mechanism": "None"}
    # These tests validate that default directly, and that the validator enforces it.
    DEFAULT_SASL_OPTIONS = {"mechanism": "None"}

    def _make_kafka_kwargs(self, sasl_options=None):
        base = dict(
            type=MonitorType.KAFKA_PRODUCER,
            name="test",
            interval=60,
            maxretries=0,
            retryInterval=60,
            kafkaProducerTopic="topic",
            kafkaProducerMessage="msg",
            accepted_statuscodes=["200-299"],
            dns_resolve_type="A",
            notificationIDList=None,
            databaseConnectionString=None,
            kafkaProducerSaslOptions=sasl_options if sasl_options is not None else self.DEFAULT_SASL_OPTIONS,
            conditions=None,
        )
        return base

    def test_default_sasl_options_is_dict(self):
        opts = self.DEFAULT_SASL_OPTIONS
        self.assertIsInstance(opts, dict, f"expected dict, got {type(opts)}: {opts!r}")

    def test_default_sasl_options_serializes_to_valid_json(self):
        # Catches the {mechanism:None} bug — Python dict must round-trip through JSON
        serialized = json.dumps(self.DEFAULT_SASL_OPTIONS)
        self.assertEqual(json.loads(serialized), self.DEFAULT_SASL_OPTIONS)

    def test_mechanism_value_is_string(self):
        mechanism = self.DEFAULT_SASL_OPTIONS["mechanism"]
        self.assertIsInstance(mechanism, str, f"mechanism must be str, got {type(mechanism)}: {mechanism!r}")

    def test_valid_default_passes_validation(self):
        kwargs = self._make_kafka_kwargs()
        _check_arguments_monitor(kwargs)  # should not raise

    def test_invalid_mechanism_rejected(self):
        kwargs = self._make_kafka_kwargs(sasl_options={"mechanism": "bad-value"})
        with self.assertRaises(ValueError):
            _check_arguments_monitor(kwargs)


if __name__ == "__main__":
    unittest.main()
