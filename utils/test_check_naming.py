from unittest import TestCase

from utils.check_naming import check_format


class TestNaming(TestCase):
    def test_check_format(self):
        self.assertTrue(check_format("1.2.3"))
        self.assertFalse(check_format("1.2.3."))
        self.assertFalse(check_format(""))
        self.assertFalse(check_format("1 2.3"))
        self.assertFalse(check_format("1-2.3"))
        self.assertFalse(check_format("1_2.3"))
        self.assertTrue(check_format("abc.cde.efg"))
        self.assertFalse(check_format("abc."))
        self.assertFalse(check_format("abc..efg"))
        self.assertFalse(check_format("."))
