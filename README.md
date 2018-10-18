
# Sentry
Watch Linux processes and notify when they complete. Should also work with MacOS*.

Only needs the */proc* pseudo-filesystem to check and gather information about processes. Does not need to create/own the process, if you want a daemon manager, see the *Alternatives* section below.

Currently written for **Python3**, but shouldn't be difficult to make python2 compatible.

\**If you run process-watcher on MacOS and it works, let me know so I can update the documentation.* 

**Supported notification methods:**

* Console (STDOUT)
* Email
* Desktop Notification

**Example output message**

*Sent in body of messages. Other information from /proc/PID/status can easily be added by modifying the code.*
```
PID 18851: /usr/lib/libreoffice/program/soffice.bin --writer --splash-pipe=5
 Started: Thu, Mar 10 18:33:37  Ended: Thu, Mar 10 18:34:26  (duration 0:00:49)
 Memory (current/peak) - Resident: 155,280 / 155,304 kB   Virtual: 1,166,968 / 1,188,216 kB
```

## Help

Access script help with `-h`, `--help`, or no arguments at all.

```
usage: process_watcher.py [-h] [-p PID] [-c COMMAND_PATTERN]
                          [-crx COMMAND_REGEX] [-w] [--to EMAIL_ADDRESS]
                          [--channel CHANNEL] [-n] [-i SECONDS] [-q] [--log]
                          [--tag LABEL] [-l LOGIN] [--password PASSWORD]
                          [--smtp SMTP]

Watch a process and notify when it completes via various communication protocols.
(See README.md for help installing dependencies)

A simple invocation:

$ (prog)s -p 123 --to me@email.com

A more complex invocation:
 ([+] indicates the argument may be specified multiple times)

$ process_watcher.py -p 1234 -p 4258 -c myapp* -crx "exec\d+" --to person1@domain.com --to person2@someplace.com

optional arguments:
  -h, --help            show this help message and exit
  -p PID, --pid PID     process ID(s) to watch [+].
  -c COMMAND_PATTERN, --command COMMAND_PATTERN
                        watch all processes matching the command name pattern. (shell-style wildcards) [+].
  -crx COMMAND_REGEX, --command-regex COMMAND_REGEX
                        watch all processes matching the command name regular expression. [+].
  -w, --watch-new       watch for all new processes that match -c|--command.
  --to EMAIL_ADDRESS    email address to send to [+].
  --channel CHANNEL     Slack channel to send to [+].)
  -n, --notify          send DBUS Desktop notification
  -i SECONDS, --interval SECONDS
                        how often to check on processes. (default: 15.0 seconds).
  -q, --quiet           don't print anything to stdout except warnings and errors
  --log                 log style output (timestamps and log level)
  --tag LABEL           label for process [+]
  -l LOGIN, --login LOGIN
                        Originating Mail account (default GMAIL env variable).
  --password PASSWORD   Password for the account specified in -l|-login. Defaults to env variable GPASSWORD.
  --smtp SMTP           SMTP server address for email service. (default GMAIl)
```

# Installation

Just create a symbolic link to **sentry.py**

For example: `ln -s /path/to/sentry/sentry.py /usr/local/bin/sentry` or for a local install `ln -s /path/to/sentry/sentry.py /home/username/bin/sentry`

# Running

The program just runs until all processes end or forever if *--watch-new* is specified.

In Unix environments you can run a program in the background and disconnect from the terminal like this:

`$ nohup sentry -p 1234 [options] &` 

This can also be done neatly in a one-liner, with the `bash` variable `$!` which captures the previous commands PID:

`$ somecommand & nohup sentry -p $! &`

Note, since `somecommand` is not disowned, this is best used inside `screen` or `tmux` where a hangup isnt sent.

## Examples
Send an email when process 1234 exits.

`process_watcher --pid 1234 --to me@gmail.com`

Watch all **myapp** processes and continue to watch for new ones. Send desktop notifications.

`process_watcher --command myapp --notify --watch-new`

Watch 2 PIDs, continue to watch for multiple command name patterns, email two people.

`process_watcher -p 4242 -p 5655 -c myapp -c anotherapp -c "kworker/[24]" -w --to bob@gmail.com --to alice@gmail.com`


# Optional Dependencies

## Desktop Notifications

Requires [notify2](https://notify2.readthedocs.org/en/latest)

`python3 -m pip install notify2`

Requires **python-dbus**, which is easiest to install with your package manager:

`sudo apt-get install python3-dbus`

## Email

Uses Python's built-in email module, however email configuration will be required. By default, you can give the script a Gmail account and password (directly, or stored as the environment variables `$GMAIL` and `$GPASSWORD`. It's up to you how you elect to secure this.

If you want to use a different email client, you will need to alter the parameters: `--smtp`, `-l|--login`, and `--password`, to suit.


# Ideas & Bugs
- Record other proc stats
- Rare race condition where a PID is found but ends before /proc/PID is read.
- Package up, so installable easily with pip
- Alert on high-memory and high-CPU usage
- Add --command-args option
- Refactor to support wrapping a command? e.g. `sentry command [args] &`
- RegEx flags
