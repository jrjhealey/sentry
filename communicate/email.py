
import logging
import smtplib
from email.mime.text import MIMEText


def send(login, password, to=None, process=None, subject_format='{executable} process {pid} ended'):
    """Send email about the ended process.

    :param to: email addresses to send to
    :param process: information about process. (.info() inserted into body)
    :param subject_format: subject format string. (uses process.__dict__)
    """
    if to is None:
        raise ValueError('to keyword arg required')

    body = process.info()
    body += '\n\n(automatically sent by process-watcher program)'
    msg = MIMEText(body)
    msg['Subject'] = subject_format.format(**process.__dict__)
    # From is required
    msg['From'] = 'Sentinel@'
    msg['To'] = ', '.join(to)

    # Send the message via our own SMTP server.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login(login, password)
    try:
        logging.info('Sending email to: {}'.format(msg['To']))
        print(msg)
        s.sendmail("jrj.healey@gmail.com", "jrj.healey@gmail.com", str(msg))
    finally:
        s.quit()
