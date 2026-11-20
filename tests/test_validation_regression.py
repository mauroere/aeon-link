"""Regression: do not rely on jsonschema's optional date-time FormatChecker."""
import copy
import unittest
from unittest.mock import patch
from aeon_link import message, validate_envelope, ProtocolError


def example():
    return message('task','alpha','beta',{
      'objective':{'id':'x','text':'Verify source','success_criteria':['Confirm']},
      'constraints':{'read_only':True},'action':'observe','claims':[],
      'evidence':[{'id':'e','source_uri':'urn:example',
                   'observed_at':'2026-11-20T14:00:00Z'}]})


class TestDateRegression(unittest.TestCase):
    def test_invalid_dates_fail_without_optional_format_checker(self):
        class LenientSchema:
            def iter_errors(self, value):
                return iter(())
        invalid=('2026-15-99T25:61:00Z','not a timestamp','2026-11-20',
                 '2026-02-29T08:01:59Z','2026-01-01T00:00:00+99:99',
                 '2026-02-30T00:00:00Z','0000-01-01T00:00:00Z')
        with patch('aeon_link.core.VALIDATOR', LenientSchema()):
            for value in invalid:
                with self.subTest(value=value):
                    obj=copy.deepcopy(example())
                    obj['body']['evidence'][0]['observed_at']=value
                    with self.assertRaisesRegex(ProtocolError,'date-time'):
                        validate_envelope(obj)
    def test_valid_leap_date(self):
        obj=example()
        obj['body']['evidence'][0]['observed_at']='2028-02-29T08:01:59Z'
        self.assertTrue(validate_envelope(obj))

if __name__=='__main__':unittest.main()
