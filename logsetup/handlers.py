"""
Additional handlers, not necessarily for use in logsetup.
"""

import logging
import pyprowl
import mailgun_api


class ProwlHandler(logging.Handler):
	"""
	Handler for sending formatted log records to iOS devices using Prowl.

	For more info, check
	https://www.prowlapp.com/
	"""
	def __init__(self, api_key, app_name, event, header="", priority=0, url=None):
		"""
		Initializes the handler.

		args:
			api_key (str): Your Prowl API key, generated on the site's account page.
			app_name (str): Unique identifier for this application, sent with each notification.
			event (str): Title of the notification.
			header (str): Text sent directly before the logged message.
			priority (int): Priority of the notification, ranging from -2 (very low) to 2 (emergency)
			url (str): URL to send along with the notification
		"""
		logging.Handler.__init__(self)
		self.api_key = api_key
		self.app_name = app_name
		self.event = event
		self.header = header
		self.priority = priority
		self.url = url

	def get_event(self, record):
		"""
		Determine the event for the notification.

		To specify a record-independent event, override this method.
		"""
		return self.event

	def get_description(self, record):
		"""
		Determine the description for the notification.

		To specify a record-independent description, override this method.
		"""
		return self.header + "\n" + self.format(record)

	def emit(self, record):
		try:
			event = self.get_event(record)
			description = self.get_description(record)
			prowl = pyprowl.Prowl(self.api_key, self.app_name)
			prowl.notify(event=event, description=description, priority=self.priority, url=self.url, appName=self.app_name)
		except:
			self.handleError(record)

class MailgunHandler(logging.Handler):
	"""
	Handler for sending emails with formatted log records using the Mailgun API

	For more info, and to get an API key, check
	https://www.mailgun.com/
	"""
	def __init__(self, api_key, domain, sender, to, subject=None, header=""):
		logging.Handler.__init__(self)
		self.api_key = api_key
		self.domain = domain
		self.sender = sender
		self.to = to
		self.subject = subject
		self.header = header

	def get_subject(self, record):
		"""
		Determine the subject for the email.

		To specify a record-independent subject, override this method.
		"""
		return self.subject

	def get_body(self, record):
		"""
		Determine the body for the email.

		To specify a record-independent body, override this method.
		This is commonly used to provide nonsensitive debug info
		which may be of use when troubleshooting errors.
		"""
		return self.header + "\n" + self.format(record)

	def emit(self, record):
		try:
			subject = self.get_subject(record)
			body = self.get_body(record)
			mg = mailgun_api.MailgunAPI(self.api_key, self.domain)
			mg.send_message(self.sender, self.to, self.subject, body)
		except:
			self.handleError(record)
