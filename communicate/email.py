
import logging
import smtplib
from email.mime.text import MIMEText


def send(login=None, password=None, smtp=None, to=None, process=None, subject_format='{executable} process {pid} ended'):
    """Send email about the ended process.

    :param to: email addresses to send to
    :param process: information about process. (.info() inserted into body)
    :param subject_format: subject format string. (uses process.__dict__)
    """
    if to is None:
        raise ValueError('to keyword arg required')
    if to is not None:
        if login is None or password is None:
            raise ValueError('login and password are needed')


    body = process.info()
    body += '\n\n(This email was auto-generated by SENTRY)'
    msg = MIMEText(body)
    msg['Subject'] = subject_format.format(**process.__dict__)
    # From is required
    msg['From'] = 'Sentinel@'
    msg['To'] = ', '.join(to)

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(smtp)
    s.starttls()
    s.login(login, password)
    try:
        logging.info('Sending email to: {}'.format(msg['To']))
        print(msg)
        s.sendmail(login, to, str(msg))
    finally:
        s.quit()
