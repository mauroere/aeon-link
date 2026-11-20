import unittest
from unittest.mock import patch
from aeon_link.providers import ask_model, ProviderError

class ProviderAdaptersTest(unittest.TestCase):
    def test_no_credential_no_network(self):
        with patch('aeon_link.providers.build_opener') as call:
            with self.assertRaises(ProviderError):
                ask_model('openai','test-model','hello',api_key='')
            call.assert_not_called()
    def test_reject_invalid_model(self):
        with self.assertRaises(ProviderError):
            ask_model('gemini','model/../../x','hello',api_key='demo')
    def test_mock_openai(self):
        def respond(url,payload,headers,timeout):
            self.assertEqual(url,'https://api.openai.com/v1/responses')
            self.assertFalse(payload['store'])
            return {'output':[{'type':'message','content':[{'type':'output_text','text':'ok'}]}], 'usage':{'input_tokens':5,'output_tokens':1}}
        with patch('aeon_link.providers._post',side_effect=respond):
            r=ask_model('openai','gpt-example','prompt',api_key='demo')
        self.assertEqual((r.text,r.input_tokens,r.output_tokens),('ok',5,1))
    def test_mock_anthropic(self):
        with patch('aeon_link.providers._post',return_value={'content':[{'type':'text','text':'ok'}], 'usage':{'input_tokens':2,'output_tokens':1}}):
            self.assertEqual(ask_model('anthropic','claude-example','hello',api_key='demo').text,'ok')
    def test_mock_gemini(self):
        with patch('aeon_link.providers._post',return_value={'candidates':[{'content':{'parts':[{'text':'ok'}]}}], 'usageMetadata':{'promptTokenCount':2,'candidatesTokenCount':1}}):
            self.assertEqual(ask_model('gemini','gemini-example','hello',api_key='demo').text,'ok')
    def test_no_raw_error_response_leak(self):
        with patch('aeon_link.providers._post',return_value={'error':{'message':'secret'}}):
            with self.assertRaises(ProviderError) as err:
                ask_model('gemini','model','hello',api_key='demo')
        self.assertNotIn('secret',str(err.exception))

if __name__=='__main__':unittest.main()
