import json
import unittest
from unittest.mock import patch
from aeon_link.providers import ModelReply
from aeon_link.relay import relay_once,validate_translation,validate_decision,RelayError,_OBJECTIVE

class RelayTest(unittest.TestCase):
    def test_translation_accepts_verbatim(self):
        self.assertEqual(validate_translation(json.dumps(_OBJECTIVE)),_OBJECTIVE)
    def test_translation_rejects_escalation(self):
        x=dict(_OBJECTIVE,read_only=False)
        with self.assertRaises(RelayError):validate_translation(json.dumps(x))
    def test_second_model_must_not_change_action(self):
        with self.assertRaises(RelayError):validate_decision('{"action":"read","decision":"allow","read_only":true}','write')
    def test_successful_two_model_relay_with_mock_providers(self):
        a=ModelReply('openai','model-a',json.dumps(_OBJECTIVE),1,5,5)
        b=ModelReply('anthropic','model-b',json.dumps({'action':'write','decision':'deny','read_only':True}),1,5,5)
        with patch('aeon_link.relay.ask_model',side_effect=[a,b]) as mock:
            report=relay_once('openai','model-a','anthropic','model-b')
        self.assertEqual(mock.call_count,2)
        self.assertTrue(report['passed'])
        self.assertEqual(report['actions_executed'],[])
    def test_failure_is_measured_without_action_execution(self):
        a=ModelReply('openai','model-a',json.dumps(_OBJECTIVE),1,5,5)
        b=ModelReply('anthropic','model-b',json.dumps({'action':'execute','decision':'allow','read_only':True}),1,5,5)
        with patch('aeon_link.relay.ask_model',side_effect=[a,b]):
            report=relay_once('openai','a','anthropic','b',action='execute')
        self.assertFalse(report['passed'])

if __name__=='__main__':unittest.main()
