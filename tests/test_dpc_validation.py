
import unittest
import sys, os
sys.path.insert(0, os.path.abspath("UCIL_Enterprise_Platform_v3.5/03_Core_Engine_Source"))
from ucil_engine.pipeline import UCILPipeline
from ucil_engine.dpc import GateVerdictEnum

class TestDPCValidation(unittest.TestCase):
    def setUp(self):
        self.pipeline = UCILPipeline()
        self.sample = "을은 30일 이내에 지급한다. 고의 또는 중과실로 인한 손해는 제외한다."

    def test_dpc_compilation(self):
        cio, dpc = self.pipeline.create_dpc(self.sample, {
            "target_identity_name": "TIME_PAYMENT_GRACE",
            "new_value": "60일 이내에 지급"
        })
        self.assertEqual(len(dpc.change_obligations), 1)
        self.assertTrue(len(dpc.non_regression_obligations) >= 1)
        self.assertEqual(dpc.change_obligations[0].required_state, "60일 이내에 지급")
