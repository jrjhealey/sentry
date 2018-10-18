#!/usr/bin/env python3

import os
import sys
import argparse
from argparse import RawTextHelpFormatter
import logging
from process import *

__author__ = "Joe R. J. Healey (based upon Arlo White's original)"
__version__ = "0.1"
__title__ = "Sentry"
__license__ = "GPLv3"
__author_email__ = "jrj.healey@gmail.com"

# TODO:
# Figure out how to support a generalised email service?

def get_args():
    '''Process command line arguments.'''
    try:
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                 description="""Watch a process and notify when it completes via various \
communication protocols.
(See README.md for help installing dependencies)

A simple invocation:

$ (prog)s -p 123 --to me@email.com

A more complex invocation:
 ([+] indicates the argument may be specified multiple times)

$ %(prog)s -p 1234 -p 4258 -c myapp* -crx "exec\d+" --to person1@domain.com --to person2@someplace.com
""")

        parser.add_argument('-p', '--pid', type=int, action='append', default=[],
                            help='process ID(s) to watch [+].')
        parser.add_argument('-c', '--command', action='append', default=[], metavar='COMMAND_PATTERN',
                            help='watch all processes matching the command name pattern. (shell-style wildcards) [+].')
        parser.add_argument('-crx', '--command-regex', action='append', default=[], metavar='COMMAND_REGEX',
                            help='watch all processes matching the command name regular expression. [+].')
        parser.add_argument('-w', '--watch-new', action='store_true',
                            help='watch for all new processes that match -c|--command.')
        parser.add_argument('--to', action='append', metavar='EMAIL_ADDRESS',
                            help='email address to send to [+].')
        parser.add_argument('--channel', action='append',
                            help='Slack channel to send to [+].)')
        parser.add_argument('-n', '--notify', action='store_true',
                            help='send DBUS Desktop notification')
        parser.add_argument('-i', '--interval', type=float, default=15.0, metavar='SECONDS',
                            help='how often to check on processes. (default: 15.0 seconds).')
        parser.add_argument('-q', '--quiet', action='store_true',
                            help="don't print anything to stdout except warnings and errors")
        parser.add_argument('--log', action='store_true',
                            help="log style output (timestamps and log level)")
        parser.add_argument('--tag', help='label for process [+]', action='append', metavar='LABEL')
        parser.add_argument('-l', '--login', action='store', default=os.environ.get('GMAIL', None), type=str,
                            help="Originating Mail account (default GMAIL env variable).")
        parser.add_argument('--password', action='store', default=os.environ.get('GPASSWORD', None), type=str,
                            help='Password for the account specified in -l|-login. Defaults to env variable GPASSWORD.')
        parser.add_argument('--smtp', action='store', default='smtp.gmail.com:587',
                            help='SMTP server address for email service. (default GMAIl)')
    
        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

    except NameError:
        sys.stderr.write('An exception occurred while parsing arguments, double check the provided arguments.')
        
    return  parser.parse_args()


def main():
    '''Main function. Coordinates polling of process and submitting notifications.'''
    
    args = get_args()
    log_level = logging.WARNING if args.quiet else logging.INFO
    log_format = '%(asctime)s %(levelname)s: %(message)s' if args.log else '%(message)s'
    logging.basicConfig(format=log_format, level=log_level)
    # Load communication protocols based present arguments
    # (library, send function keyword args)
    comms = []
    if args.to:
        try:
            import communicate.email
            comms.append((communicate.email, {'to': args.to}))
        except:
            logging.exception('Failed to load email module. (required by --to)')
            sys.exit(1)

    if args.channel:
        try:
            import communicate.slack
            comms.append((communicate.slack, {'channel': args.channel}))
        except:
            logging.exception('Failed to load slack module. (required by --channel)')
            sys.exit(1)

    if args.notify:
        exception_message = 'Failed to load Desktop Notification module. (required by --notify)'
        try:
            import communicate.dbus_notify
            comms.append((communicate.dbus_notify, {}))
        except ImportError as err:
            if err.name == 'notify2':
                logging.error("{}\n 'notify2' python module not installed.\n"
                              " pip install notify2"
                              " (you also need to install the python3-dbus system package)".format(exception_message))
            else:
                logging.exception(exception_message)
                sys.exit(1)
        except:
            logging.exception(exception_message)
            sys.exit(1)

    watched_processes = {}

    # Initialize processes from arguments, get metadata
    for pid in args.pid:
        try:
            if pid not in watched_processes:
                watched_processes[pid] = ProcessByPID(pid)

        except NoProcessFound as ex:
            logging.warning('No process with PID {}'.format(ex.pid))

    process_matcher = ProcessMatcher()
    new_processes = ProcessIDs()
    for pattern in args.command:
        process_matcher.add_command_wildcard(pattern)

    for regex in args.command_regex:
        process_matcher.add_command_regex(regex)

    for pid in process_matcher.matching(new_processes):
        if pid not in watched_processes:
            watched_processes[pid] = ProcessByPID(pid)

    watch_new = args.watch_new and process_matcher.num_conditions > 0

    if not watched_processes and not watch_new:
        logging.warning('No processes found to watch.')
        sys.exit(1)

    logging.info('Watching {} process(es):'.format(len(watched_processes)))
    for pid, process in watched_processes.items():
        logging.info(process.info())

    try:
        to_delete = []
        while True:
            time.sleep(args.interval)
            for pid, process in watched_processes.items():
                try:
                    running = process.check()
                    if not running:
                        to_delete.append(pid)
                        logging.info('Process stopped\n%s', process.info())
                        for comm, send_args in comms:
                            if args.tag:
                                template = '{executable} process {pid} ended' + ': {}'.format(args.tag)
                            else:
                                template = '{executable} process {pid} ended'
                            comm.send(args.login, args.password, args.smtp, process=process, subject_format=template, **send_args)
                except:
                    logging.exception('Exception encountered while checking or communicating about process {}'.format(pid))
                    if pid not in to_delete:
                        to_delete.append(pid)

            if to_delete:
                for pid in to_delete:
                    del watched_processes[pid]
                to_delete.clear()

            if watch_new:
                for pid in process_matcher.matching(new_processes):
                    try:
                        watched_processes[pid] = p = ProcessByPID(pid)
                        logging.info('watching new process\n%s', p.info())
                    except:
                        logging.exception('Exception encountered while attempting to watch new process {}'.format(pid))
            elif not watched_processes:
                sys.exit(1)

    except KeyboardInterrupt:
        print()

if __name__ == '__main__':
    main()
