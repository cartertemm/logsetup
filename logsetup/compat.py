import threading


def ensure_threaded_excepthook():
	# threading.excepthook is new as of version 3.8
	# for previous versions, see python bug
	# http://bugs.python.org/issue1230540
	try:
		threading.excepthook
	except AttributeError:
		# backport Python implementation
		# mostly from lib/threading.py
		from collections import namedtuple
		_ExceptHookArgs = namedtuple('ExceptHookArgs', 'exc_type exc_value exc_traceback thread')
		def ExceptHookArgs(args):
			return _ExceptHookArgs(*args)

		def _make_invoke_excepthook():
			# Create a local namespace to ensure that variables remain alive
			# when _invoke_excepthook() is called, even if it is called late during
			# Python shutdown. It is mostly needed for daemon threads.
			old_excepthook = excepthook
			old_sys_excepthook = sys.excepthook
			if old_excepthook is None:
				raise RuntimeError("threading.excepthook is None")
			if old_sys_excepthook is None:
				raise RuntimeError("sys.excepthook is None")
			sys_exc_info = sys.exc_info
			local_print = print
			local_sys = sys

			def invoke_excepthook(thread):
				try:
					hook = threading.excepthook
					if hook is None:
						hook = old_excepthook
					args = ExceptHookArgs([*sys_exc_info(), thread])
					hook(args)
				except Exception as exc:
					exc.__suppress_context__ = True
					del exc
					if local_sys is not None and local_sys.stderr is not None:
						stderr = local_sys.stderr
					else:
						stderr = thread._stderr
					local_print("Exception in threading.excepthook:",
								file=stderr, flush=True)
					if local_sys is not None and local_sys.excepthook is not None:
						sys_excepthook = local_sys.excepthook
					else:
						sys_excepthook = old_sys_excepthook
					sys_excepthook(*sys_exc_info())
				finally:
					# Break reference cycle (exception stored in a variable)
					args = None

			return invoke_excepthook

		def excepthook(args):
			"""
			Handle uncaught Thread.run() exception.
			"""
			if args.exc_type == SystemExit:
				# silently ignore SystemExit
				return
			if sys is not None and sys.stderr is not None:
				stderr = sys.stderr
			elif args.thread is not None:
				stderr = args.thread._stderr
				if stderr is None:
					# do nothing if sys.stderr is None and sys.stderr was None
					# when the thread was created
					return
			else:
				# do nothing if sys.stderr is None and args.thread is None
				return
			if args.thread is not None:
				name = args.thread.name
			else:
				name = get_ident()
			print(f"Exception in thread {name}:",
					file=stderr, flush=True)
			traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback,
							 file=stderr)
			stderr.flush()
		threading.excepthook = excepthook

		# monkeypatch Thread.run so that exceptions are properly sent
		thread_init = threading.Thread.__init__
		def __init__(self, *args, **kwargs):
			thread_init(self, *args, **kwargs)
			self._invoke_excepthook = _make_invoke_excepthook()
			thread_run = self.run
			def run_with_excepthook(*args2, **kwargs2):
				try:
					thread_run(*args2, **kwargs2)
				except:
					self._invoke_excepthook(self)
			self.run = run_with_excepthook
		threading.Thread.__init__ = __init__


ensure_threaded_excepthook()
