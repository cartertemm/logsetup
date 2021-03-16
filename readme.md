Logsetup eases the often tedious and repetitive process of log initialization, without compromising flexibility.

It augments the builtin logging facility by providing a straightforward API, scores of seamless third-party integrations, thread-independent exception catching, and more.

Never write another redundant logging procedure again.

## why?

Though python's builtin log facility provides a lot of flexibility and functionality straight out of the box, it unfortunately requires a lot of messy configuration, especially when used in complex applications.

To illustrate this, the following snippet is a typical log setup, where all events are printed to stderr and errors are sent to errors.log.

```
import logging

formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
error_handler = logging.FileHandler("errors.log")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
```

That was awfully verbose.

Enter logsetup!

```
import logging
import logsetup

logsetup.set_level(logging.DEBUG)

logsetup.log_to_stream(logging.DEBUG)
logsetup.log_to_file(logging.ERROR, "errors.log")
```

and we're done

```
>>> logger = logging.getLogger()
>>> logger.debug("debug message")
DEBUG root - <stdin>.<module> (2021-03-16 09:54:17) - MainThread (13828):
debug message

>>> try:
... 	0/0
... except:
... 	logger.exception("while calculating 0/0")

ERROR root - <stdin>.<module> (2021-03-16 09:55:47) - MainThread (13828):
while calculating 0/0
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
ZeroDivisionError: division by zero
>>>
```

### What about basicConfig?

logging.basicConfig works fine in tiny console applications, but due to limited scope will quickly prove inadequate for anything more sophisticated.

## How it works

The following assumes a solid understanding of logging levels, handlers, and how they interact to functionally send messages to different destinations.
If you need to quickly brush up on these concepts, have a look at the [Advanced Logging Tutorial](https://docs.python.org/3/howto/logging.html).


At the start of your application, import and initialize logsetup with a level which will be applied to the root logger.

```
import logging
import logsetup

logsetup.set_level(logging.DEBUG)
```

To log all exceptions at a severity of logging.ERROR, you can:

```
logsetup.log_unhandled_exceptions()
```

and for the same behavior across threads:

```
logsetup.log_threaded_exceptions
```

Note that `log_unhandled_exceptions` takes an optional callback, in cases where you need to notify your UI for example.

Any logging implementation would be useless without handlers, which send messages to a destination of your choosing. In logsetup, handlers are created and applied in a single `logsetup.log_to_*` function call, each of which require a severity level and variable number of parameters.

```
>>> logsetup.log_to_file(logging.DEBUG, "debug.log")
<FileHandler debug.log (DEBUG)>
```

In short, this means write out all events with a severity of DEBUG or above to "debug.log".

There is no limit to the number of handlers a given logger can have. In fact, in production you'll probably want multiple. For instance, one to print messages to the console, another to pipe everything to a file for later review, and yet another to send critical errors to your team via email or Slack.
If you have a user-facing application, it's only a matter of time before something somewhere goes wrong. With permission, get peace of mind by automatically sending diagnostic data, crashes, errors and other issues along to those that can work to develop a patch.

### Custom formats

By default, logsetup uses `logsetup.DEFAULT_FMT` and `logsetup.DEFAULT_DATEFMT` for it's log and date formatting.

If you'd like to change this for individual handlers, you can do so by passing the `fmt` and `datefmt` keyword arguments, like so:

```
fmt = "%(asctime)s %(levelname)s:%(name)s:%(message)s"
log_to_socket(logging.ERROR, host, port, fmt=fmt)
```

## Handlers

The following builtin handlers are currently supported. Refer to the code or corresponding handler's documentation for more info.

* stream - writes to IO streams
* file - writes to a file on disk
* rotating_file - writes to a set of files on disk, switching out when one reaches a certain size
* timed_rotating_file - like rotating_file, but switches out after a set time period
* socket - writes pickled records to a socket listening over TCP. Use `logging.makeLogRecord` to turn the data into a python object
* SMTP - writes to an email message, sent using the provided SMTP server

The following are implemented in logsetup directly:

* [Mailgun](https://www.mailgun.com/) - cheap and hassle free email delivery API
* [Prowl](https://www.prowlapp.com/) - sends iOS push notifications

### Notifiers Integration

If the [Notifiers](https://github.com/liiight/notifiers) packages is installed, additional logsetup handler functions will be defined at runtime for each supported provider.
Using them is as simple as:

```
logsetup.log_to_pushover(logging.ERROR, user, message, token)
logsetup.log_to_slack(logging.WARNING, webhook_url, message)
```
