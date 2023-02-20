import unittest

from ddnsmulti.change_request import ChangeRequest

CHANGE_REQUEST = """
zone: example.com
change: a.example.com
from:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
  - "a.example.com. NS ns2.b.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns2.a.example.com A 10.0.0.2"
to:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns4.a.example.com"
  - "a.example.com. NS ns2.b.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns4.a.example.com A 10.0.0.2"
  - "ns4.a.example.com AAAA 2001:67c:394:15::4"
"""

CHANGE_REQUEST_GLUE_ONLY = """
zone: example.com
change: a.example.com
from:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns2.a.example.com A 10.0.0.2"
to:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
  - "ns1.a.example.com A 10.0.0.3"
  - "ns2.a.example.com A 10.0.0.4"
"""

CHANGE_REQUEST_ZONE_MISMATCH = """
zone: example.net
change: a.example.com
from:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
  - "a.example.com. NS ns2.b.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns2.a.example.com A 10.0.0.2"
to:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns4.a.example.com"
  - "a.example.com. NS ns2.b.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns4.a.example.com A 10.0.0.2"
  - "ns4.a.example.com AAAA 2001:67c:394:15::4"
"""

CHANGE_REQUEST_OUT_OF_ZONE = """
zone: example.com
change: b.example.com
from:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns2.a.example.com A 10.0.0.2"
to:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns4.a.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns4.a.example.com A 10.0.0.2"
"""
CHANGE_REQUEST_SUPERFLOUS_GLUE = """
zone: example.com
change: a.example.com
from:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns2.a.example.com A 10.0.0.2"
  - "ns1.b.example.com A 10.0.0.3"
to:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns4.a.example.com"
  - "ns1.a.example.com A 10.0.0.1"
  - "ns4.a.example.com A 10.0.0.2"
"""

CHANGE_REQUEST_MISSING_GLUE = """
zone: example.com
change: a.example.com
from:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns2.a.example.com"
to:
  - "a.example.com. NS ns1.a.example.com"
  - "a.example.com. NS ns4.a.example.com"
"""


class TestChangeRequest(unittest.TestCase):
    def test_validate_cr(self):
        ChangeRequest.from_yaml(CHANGE_REQUEST)

    def test_out_of_zone(self):
        with self.assertRaises(ValueError):
            _ = ChangeRequest.from_yaml(CHANGE_REQUEST_OUT_OF_ZONE)

    def test_zone_mismatch(self):
        with self.assertRaises(ValueError):
            _ = ChangeRequest.from_yaml(CHANGE_REQUEST_ZONE_MISMATCH)

    def test_superflous_glue(self):
        with self.assertRaises(ValueError):
            _ = ChangeRequest.from_yaml(CHANGE_REQUEST_SUPERFLOUS_GLUE)

    def test_missing_glue(self):
        with self.assertRaises(ValueError):
            _ = ChangeRequest.from_yaml(CHANGE_REQUEST_MISSING_GLUE)

    def test_ddns(self):
        cr = ChangeRequest.from_yaml(CHANGE_REQUEST)
        message = cr.to_message()
        print(message)

    def test_ddns_glue_only(self):
        cr = ChangeRequest.from_yaml(CHANGE_REQUEST_GLUE_ONLY)
        message = cr.to_message()
        print(message)

    def test_nsupdate(self):
        cr = ChangeRequest.from_yaml(CHANGE_REQUEST)
        nsupdate = cr.to_nsupdate()
        print(nsupdate)

    def test_nsupdate_glue_only(self):
        cr = ChangeRequest.from_yaml(CHANGE_REQUEST_GLUE_ONLY)
        nsupdate = cr.to_nsupdate()
        print(nsupdate)


if __name__ == "__main__":
    unittest.main()
