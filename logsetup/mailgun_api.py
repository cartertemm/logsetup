import requests

API_USERNAME = 'api'
MAX_PER_SEND = 1000

class MailgunAPI(object):
 api_url = 'https://api.mailgun.net/v2'

 def __init__(self, api_key, domain, test_mode=False):
  self.api_key = api_key
  self.domain = domain
  self.test_mode = test_mode
  self.session = requests.session()
  self.session.auth = (API_USERNAME, api_key)

 def API_call(self, method, endpoint, files=None, **kwargs):
  send_dict = kwargs
  tags = send_dict.get('tags', [])
  if tags:
   del send_dict['tags']
   send_dict['o:tag'] = tags
  if self.test_mode:
   send_dict['o:testmode'] = True
  url = self.build_url(endpoint)
  if files is not None:
   response = method(url, data=send_dict, files=files)
  else:
   response = method(url, data=send_dict)
  response.raise_for_status()
  return response.json()

 def post(self, endpoint, **kwargs):
  return self.API_call(self.session.post, endpoint, **kwargs)

 def send_message(self, sender, to, subject=None, text=None, **kwargs):
  send_dict = dict(to=to, subject=subject, text=text, **kwargs)
  send_dict['from'] = sender
  return self.post('messages', **send_dict)

 def send_many(self, sender, to, **kwargs):
  for start in xrange(0, len(to), MAX_PER_SEND):
   self.send_message(sender, to[start:start+MAX_PER_SEND], **kwargs)



 def build_url(self, extra):
  return '%s/%s/%s' % (self.api_url, self.domain, extra)
