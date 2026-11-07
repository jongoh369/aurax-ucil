
import unittest
import sys, os
sys.path.insert(0, os.path.abspath("UCIL_Enterprise_Platform_v3.5/03_Core_Engine_Source"))
from ucil_engine.identity_extractors import ContractIdentityExtractor
from ucil_engine.cio import IdentityClass

class TestIdentityExtractors(unittest.TestCase):
    def setUp(self):
        self.extractor = ContractIdentityExtractor()
        self.sample = """제1조 을은 30일 이내에 지급한다. 총액은 금 50,000,000원으로 한다.
제2조 지체상금율은 1일당 0.1%로 한다.
제3조 고의 또는 중과실로 인한 손해는 제외한다."""

    def test_extract_price(self):
        cio = self.extractor.extract(self.sample)
        price_idents = [i for i in cio.identities if i.identity_class == IdentityClass.NUMERIC and "PRICE" in i.name]
        self.assertTrue(len(price_idents) > 0)
        self.assertEqual(price_idents[0].canonical_value, "금 50,000,000원")

    def test_extract_grace_period(self):
        cio = self.extractor.extract(self.sample)
        time_idents = [i for i in cio.identities if i.identity_class == IdentityClass.TEMPORAL]
        self.assertTrue(len(time_idents) > 0)

    def test_extract_indemnity_carveout(self):
        cio = self.extractor.extract(self.sample)
        carveout = [i for i in cio.identities if i.name == "INT_INDEMNITY_CARVEOUT"]
        self.assertTrue(len(carveout) > 0)
