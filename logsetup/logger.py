import sys
import logging.handlers
import platform
import threading
import traceback
from . import compat
from . import handlers

try:
	import notifiers.logging
	_has_notifiers = True
except (ImportError, ModuleNotFoundError):
	_has_notifiers = False

# register module-level functions for all supported notifiers
def _construct_notifier_func(provider_name):
	def wrapper(level, **defaults):
		if not _has_notifiers:
			raise RuntimeError("the Notifiers package, required for the requested handler ("+provider_name+"), was not found. Make sure it is installed")
		return add_handler(notifiers.logging.NotificationHandler, level, provider_name, defaults)
	globals()["log_to_"+provider_name] = wrapper
	wrapper.__name__ = "log_to_" + provider_name
	wrapper.__doc__ = f"""Initializes a handler to send {provider_name} notifications for the requested level.
		see the Notifiers docs for more info (including required parameters) at
		https://notifiers.readthedocs.io/en/latest/providers/index.html"""

for provider in notifiers.all_providers():
	# Mailgun support is currently implemented through another module
	# as well as in Notifiers, and is thus excluded here
	if provider == "mailgun":
		continue
	_construct_notifier_func(provider)


log = logging.getLogger()
DEFAULT_FMT = "%(levelname)s %(name)s - %(module)s.%(funcName)s (%(asctime)s) - %(threadName)s (%(thread)d):\n%(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
exc_callback = None


def add_handler(cls, level, *args, **kwargs):
	"""Add a handler to the route logger.
	note: This function is only meant to be used when adding support for one shot invocation of new handlers.
		In all other cases, you want log_to_*

	args:
		cls (subclass of logging.Handler): The handler class that is to be instantiated
		level (int or str): The logging level (must be predefined)
		args (list): Arguments that are to be passed to the handler
		kwargs (dict): In all but a few cases, these keyword arguments are passed to the handler during initialization.
			The following parameters may be specified for further customization and are subsequently not directly passed along.
			fmt: the log formatter
			datefmt: specify a specialized date format

	returns:
		logging.Handler
	"""
	fmt = kwargs.get("fmt")
	datefmt = kwargs.get("datefmt")
	if "fmt" in kwargs:
		del kwargs["fmt"]
	if "datefmt" in kwargs:
		del kwargs["datefmt"]
	fmt = fmt or DEFAULT_FMT
	datefmt = datefmt or DEFAULT_DATEFMT
	handler = cls(*args, **kwargs)
	handler.setLevel(level)
	formatter = logging.Formatter(fmt, datefmt)
	handler.setFormatter(formatter)
	log.addHandler(handler)
	return handler


def log_to_stream(level, stream=None, *args, **kwargs):
	return add_handler(logging.StreamHandler, level, stream=stream, *args, **kwargs)


def log_to_file(level, filename, *args, **kwargs):
	return add_handler(logging.FileHandler, level, filename=filename, *args, **kwargs)


def log_to_rotating_file(level, filename, maxBytes=0, backupCount=0, *args, **kwargs):
	return add_handler(logging.handlers.RotatingFileHandler, level, filename=filename, maxBytes=maxBytes, backupCount=backupCount, *args, **kwargs)


def log_to_timed_rotating_file(level, filename, when="h", interval=1, backupCount=0, *args, **kwargs):
	return add_handler(logging.handlers.TimedRotatingFileHandler, level, filename=filename, when=when, interval=interval, backupCount=backupCount, *args, **kwargs)


def log_to_socket(level, host, port):
	return add_handler(logging.handlers.SocketHandler, level, host=host, port=port)


def log_to_smtp(level, mailhost, fromaddr, toaddrs, subject, credentials=None, *args, **kwargs):
	return add_handler(logging.handlers.SMTPHandler, level, mailhost=mailhost, fromaddr=fromaddr, toaddrs=toaddrs, subject=subject, credentials=credentials, *args, **kwargs)


def log_to_prowl(level, api_key, app_name, event, *args, **kwargs):
	return add_handler(handlers.ProwlHandler, level, api_key=api_key, app_name=app_name, event=event, *args, **kwargs)


def log_to_mailgun(level, api_key, sender, to, subject=None, domain=None, *args, **kwargs):
	# attempt parsing a domain from the sender
	# if none was specified
	if not domain:
		if not ("<" in sender and ">" in sender):
			return
		domain = sender[sender.find("@"):sender.find(">")][1:]
	return add_handler(handlers.MailgunHandler, level, api_key=api_key, domain=domain, sender=sender, to=to, subject=subject, *args, **kwargs)


def log_to_notifier(level, provider, defaults={}):
	if not _has_notifiers:
		log.warning("Attempted to register a third-party notification handler, but the notifiers package could not be found")
		return
	return add_handler(notifiers.logging.NotificationHandler, level, provider, defaults)


def _excepthook(exctype, value, traceback):
	# ignore Ctrl+C in console applications
	if issubclass(exctype, KeyboardInterrupt):
		sys.__excepthook__(exctype, value, traceback)
		return
	# silently ignore SystemExit
	if issubclass(exctype, SystemExit):
		return
	# fixme: all unhandled exceptions rightly report logger._excepthook as caller
	# when it would actually be preferable to point to the erroneous module and funcname itself
	log.error("Unhandled exception", exc_info=(exctype, value, traceback))
	if callable(exc_callback):
		exc_callback(exctype, value, tb)


def _threaded_excepthook(args):
	# ignore Ctrl+C in console applications
	if issubclass(args.exc_type, KeyboardInterrupt):
		return
	# silently ignore SystemExit
	if issubclass(args.exc_type, SystemExit):
		return
	# fixme: all unhandled exceptions rightly report logger._excepthook as caller
	# when it would actually be preferable to point to the erroneous module and funcname itself
	log.error("Unhandled exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def log_unhandled_exceptions(callback=None):
	"""Start logging all unhandled exceptions to registered handlers >= logging.ERROR.
	If a callback function is specified it will be called every time an exception is processed, with parameters (exctype, value, traceback)
		Typically used to notify other parts of the application (UI) or exit altogether.
	"""
	global exc_callback
	if callback and callable(callback):
		exc_callback = callback
	sys.excepthook = _excepthook


def log_threaded_exceptions():
	"""Start logging unhandled exceptions in threads other than the main one."""
	threading.excepthook = compat._threaded_excepthook


def log_debug_info(level=logging.INFO):
	log.log(level, "python version %s", sys.version)
	log.log(level, "running on %s version %s", platform.system(), platform.version())


def init():
	log.setLevel(logging.DEBUG)
	log_to_stream(logging.DEBUG)
	log_to_file(logging.ERROR, "errors.log")
	log_unhandled_exceptions()
	log_threaded_exceptions()
	log.debug("Initialized logging subsystem")
	log_debug_info()


def shutdown():
	logging.shutdown()

if __name__ == "__main__":
	def error():
		log.info("working on something")
		0/0

	import time
	init()
	#t = threading.Thread(target=error, daemon=True)
	#t.start()
	error()
	time.sleep(0.5)
