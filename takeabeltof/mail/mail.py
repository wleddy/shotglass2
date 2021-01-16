""" My adaptation of flask_mail v 0.9.1

I want to add the ability to use oAuth to connect to gmail SMTP
servers since they no longer allow login with username and password
from un-registered / approved apps like my web apps.

This module depends on a bunch of settings variables mostly the same as
Flask-Mail with a few additions. Here is a sample setings configuration:

```python
    ## Email Sending...
    MAIL_USE_SSL = True # Use one or the other, not both
    MAIL_USE_TLS = not MAIL_USE_SSL
    MAIL_USE_OAUTH = True # when True use oAuth instead of account and password
    MAIL_USE_GMAIL_API = False
    
    MAIL_SUBJECT_PREFIX = 'something'

    # Set up to use username and password
    if not MAIL_USE_OAUTH and not MAIL_USE_GMAIL_API:
        MAIL_SERVER = 'smtp.hosting.com'
        MAIL_USERNAME = "someone@example.com"
        MAIL_PASSWORD = "myPassword"
    
        MAIL_DEFAULT_SENDER = "Your Name"
        MAIL_DEFAULT_ADDR = MAIL_USERNAME
    elif MAIL_USE_OAUTH:
        # use this setup for oAuth
        MAIL_SERVER = 'smtp.gmail.com'
        MAIL_USERNAME = "someone@gmail.com"
        TOKEN_REQUEST_URL = "https://accounts.google.com"
        MAIL_USE_TLS = True
        MAIL_USE_SSL = False
        CLIENT_ID = '<Your Client ID>'
        CLIENT_SECRET = '< your secret >'
        REFRESH_TOKEN = '< your refresh token >'
    
        MAIL_DEFAULT_SENDER = "Your Name"
        MAIL_DEFAULT_ADDR = MAIL_USERNAME
    else:
        # use the gmail api
        # the pickle file at MAIL_TOKEN_PATH must already exist with user credentials
        MAIL_DEFAULT_SENDER = "Sender Name"
        MAIL_DEFAULT_ADDR = '<some address>@gmail.com'
        MAIL_TOKEN_PATH = 'instance/gmail_api_token.pickle' # where the credentials are stored

    if MAIL_USE_SSL:
        MAIL_PORT = 465 #465 is the SSL port
    else:
        MAIL_PORT= 587 #587 is the TLS port
```

See `google_oAuth` directory for instuctions on getting your client ID and refresh tokens from Google.

Original docstring:

flaskext.mail
~~~~~~~~~~~~~

Flask extension for sending email.

:copyright: (c) 2010 by Dan Jacob.
:license: BSD, see LICENSE for more details.
Args: None

Returns:  None

Raises: 
    MailSettingsError
    BadHeaderError
    
"""

# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
import pickle
from pdb import set_trace
import re
import smtplib
import sys
import time
import unicodedata

from email import charset
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, formataddr, make_msgid, parseaddr

# Gmail API utils
from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.mail import oauth

class BadHeaderError(Exception):
    pass

class MailSettingsError(Exception):
    pass

class Connection:
    """Handles connection to host."""
    
    def __init__(self, mail):
        self.mail = mail

    def __enter__(self):
        if self.mail.suppress:
            self.host = None
        else:
            self.host = self.configure_host()

        self.num_emails = 0

        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.host:
            self.host.quit()

    def configure_host(self):
        # import pdb;pdb.set_trace()
        if self.mail.use_oauth:
            host = oauth.get_host_connection(self.mail)
        else:
            # login with username and email
            if self.mail.use_ssl:
                host = smtplib.SMTP_SSL(self.mail.server, self.mail.port)
            else:
                host = smtplib.SMTP(self.mail.server, self.mail.port)
                
            if self.mail.use_tls:
                host.starttls()
            if self.mail.username and self.mail.password:
                host.login(self.mail.username, self.mail.password)

        host.set_debuglevel(int(self.mail.debug))

        return host

    def send(self, message, envelope_from=None):
        """Verifies and sends message.

        :param message: Message instance.
        :param envelope_from: Email address to be used in MAIL FROM command.
        """
        assert message.send_to, "No recipients have been added"
        
        assert message.sender, (
                "The message does not specify a sender and a default sender "
                "has not been configured")

        if message.has_bad_headers():
            raise BadHeaderError

        if message.date is None:
            message.date = time.time()

        if self.host: # host is None when testing
            message.failed_recipients = self.host.sendmail(sanitize_address(envelope_from or message.sender),
                                list(sanitize_addresses(message.send_to)),
                                message.as_bytes() if PY3 else message.as_string(),
                                message.mail_options,
                                message.rcpt_options)
                                
            # failed_recipients contains a dict of recipients that were refused
            if message.failed_recipients:
                pass
                
              
        self.num_emails += 1

        if self.num_emails == self.mail.max_emails:
            self.num_emails = 0
            if self.host:
                self.host.quit()
                self.host = self.configure_host()


PY3 = sys.version_info[0] == 3

PY34 = PY3 and sys.version_info[1] >= 4

if PY3:
    string_types = str,
    text_type = str
    from email import policy
    message_policy = policy.SMTP
else:
    string_types = basestring,
    text_type = unicode
    message_policy = None

charset.add_charset('utf-8', charset.SHORTEST, None, 'utf-8')


class FlaskMailUnicodeDecodeError(UnicodeDecodeError):
    def __init__(self, obj, *args):
        self.obj = obj
        UnicodeDecodeError.__init__(self, *args)

    def __str__(self):
        original = UnicodeDecodeError.__str__(self)
        return '%s. You passed in %r (%s)' % (original, self.obj, type(self.obj))


def force_text(s, encoding='utf-8', errors='strict'):
    """
    Similar to smart_text, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, text_type):
        return s

    try:
        if not isinstance(s, string_types):
            if PY3:
                if isinstance(s, bytes):
                    s = text_type(s, encoding, errors)
                else:
                    s = text_type(s)
            elif hasattr(s, '__unicode__'):
                s = s.__unicode__()
            else:
                s = text_type(bytes(s), encoding, errors)
        else:
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(s, Exception):
            raise FlaskMailUnicodeDecodeError(s, *e.args)
        else:
            s = ' '.join([force_text(arg, encoding, strings_only,
                    errors) for arg in s])
    return s

def sanitize_subject(subject, encoding='utf-8'):
    try:
        subject.encode('ascii')
    except UnicodeEncodeError:
        try:
            subject = Header(subject, encoding).encode()
        except UnicodeEncodeError:
            subject = Header(subject, 'utf-8').encode()
    return subject

def sanitize_address(addr, encoding='utf-8'):
    if isinstance(addr, string_types):
        addr = parseaddr(force_text(addr))
    nm, addr = addr

    try:
        nm = Header(nm, encoding).encode()
    except UnicodeEncodeError:
        nm = Header(nm, 'utf-8').encode()
    try:
        addr.encode('ascii')
    except UnicodeEncodeError:  # IDN
        if '@' in addr:
            localpart, domain = addr.split('@', 1)
            localpart = str(Header(localpart, encoding))
            domain = domain.encode('idna').decode('ascii')
            addr = '@'.join([localpart, domain])
        else:
            addr = Header(addr, encoding).encode()
    return formataddr((nm, addr))


def sanitize_addresses(addresses, encoding='utf-8'):
    return map(lambda e: sanitize_address(e, encoding), addresses)


def _has_newline(line):
    """Used by has_bad_header to check for \\r or \\n"""
    if line and ('\r' in line or '\n' in line):
        return True
    return False

class Mail:
    def __init__(self, server=None, username=None, password=None, port=None, use_tls=None, use_ssl=None, use_oauth=None,
                 default_sender_name=None, default_sender_addr=None, debug=None, max_emails=None, suppress=None,
                 ascii_attachments=False):
                 
        site_config = get_site_config()
        
        self.server = server if server else site_config.get('MAIL_SERVER', '127.0.0.1')
        self.username = username if username else site_config.get('MAIL_USERNAME')
        self.password = password if password else site_config.get('MAIL_PASSWORD')
        self.port = port if port else site_config.get('MAIL_PORT', None)
        self.use_tls = use_tls if use_tls else site_config.get('MAIL_USE_TLS', False)
        self.use_ssl = use_ssl if use_ssl else site_config.get('MAIL_USE_SSL', False)
        self.use_oauth = use_oauth if use_oauth else site_config.get('MAIL_USE_OAUTH', False)
        self.default_sender_name = default_sender_name if default_sender_name else site_config.get('MAIL_DEFAULT_SENDER')
        self.default_sender_addr = default_sender_addr if default_sender_addr else site_config.get('MAIL_DEFAULT_ADDR')
        self.debug = debug if debug else int(site_config.get('MAIL_DEBUG', site_config.get('DEBUG',0)))
        self.max_emails = max_emails if max_emails else site_config.get('MAIL_MAX_EMAILS')
        self.suppress = suppress if suppress else site_config.get('MAIL_SUPPRESS_SEND',  site_config.get('TESTING',False))
        self.ascii_attachments = ascii_attachments if ascii_attachments else site_config.get('MAIL_ASCII_ATTACHMENTS', False)
        
        if self.use_oauth:
            self.token_request_url = site_config['TOKEN_REQUEST_URL']
            self.client_id = site_config['CLIENT_ID']
            self.client_secret = site_config['CLIENT_SECRET']
            self.refresh_token = site_config['REFRESH_TOKEN']
            self.use_ssl = False
            self.use_tls = True
            self.port = None # set properly below

        if not self.port:
            if self.use_tls and self.use_ssl:
                raise MailSettingsError('USE_TLS and USE_SSL may not both be True')
            if self.use_tls:
                self.port = 587
            elif self.use_ssl:
                self.port = 465
            else:
                self.port = 25

    def send(self, message):
        """Sends a single message instance. If TESTING is True the message will
        not actually be sent.

        :param message: a Message instance.
        """
        # import pdb;pdb.set_trace()
        if isinstance(message,GmailAPIMessage):
            # GmailAPIMessage messages handle their own RESTful connection
            message.send(self)
        else:
            with Connection(self) as connection:
                connection.send(message)
            

class Attachment(object):
    """Encapsulates file attachment information.

    :versionadded: 0.3.5

    :param filename: filename of attachment
    :param content_type: file mimetype
    :param data: the raw file data
    :param disposition: content-disposition (if any)
    """

    def __init__(self, filename=None, content_type=None, data=None,
                 disposition=None, headers=None):
        self.filename = filename
        self.content_type = content_type
        self.data = data
        self.disposition = disposition or 'attachment'
        self.headers = headers or {}


class Message:
    """Encapsulates an email message.

    :param subject: email subject header
    :param recipients: list of email addresses
    :param body: plain text message
    :param html: HTML message
    :param sender: email sender address, or **MAIL_DEFAULT_SENDER** by default
    :param cc: CC list
    :param bcc: BCC list
    :param attachments: list of Attachment instances
    :param reply_to: reply-to address
    :param date: send date
    :param charset: message character set
    :param extra_headers: A dictionary of additional headers for the message
    :param mail_options: A list of ESMTP options to be used in MAIL FROM command
    :param rcpt_options:  A list of ESMTP options to be used in RCPT commands
    """

    def __init__(self, subject='',
                 recipients=None,
                 body=None,
                 html=None,
                 sender=None,
                 cc=None,
                 bcc=None,
                 attachments=None,
                 reply_to=None,
                 date=None,
                 charset=None,
                 extra_headers=None,
                 mail_options=None,
                 rcpt_options=None):

        # import pdb; pdb.set_trace()

        if isinstance(sender, tuple):
            sender = "%s <%s>" % sender

        self.recipients = recipients or []
        self.subject = subject
        self.sender = sender
        self.reply_to = reply_to
        self.cc = cc or []
        self.bcc = bcc or []
        self.body = body
        self.html = html
        self.date = date
        self.msgId = make_msgid()
        self.charset = charset
        self.extra_headers = extra_headers
        self.mail_options = mail_options or []
        self.rcpt_options = rcpt_options or []
        self.attachments = attachments or []
        self.failed_recipients = None   # filled by Connection.send if any recipients were refused.
                                        # Note that if all recipients are refused this is still None and the 
                                        #smtplib.SMTPRecipientsRefused is raised intead
                                        
    @property
    def send_to(self):
        return set(self.recipients) | set(self.bcc or ()) | set(self.cc or ())

    def _mimetext(self, text, subtype='plain'):
        """Creates a MIMEText object with the given subtype (default: 'plain')
        If the text is unicode, the utf-8 charset is used.
        """
        charset = self.charset or 'utf-8'
        return MIMEText(text, _subtype=subtype, _charset=charset)

    def _message(self):
        """Creates the email"""
        ascii_attachments = False
        encoding = self.charset or 'utf-8'

        attachments = self.attachments or []

        if len(attachments) == 0 and not self.html:
            # No html content and zero attachments means plain text
            msg = self._mimetext(self.body)
        elif len(attachments) > 0 and not self.html:
            # No html and at least one attachment means multipart
            msg = MIMEMultipart()
            msg.attach(self._mimetext(self.body))
        else:
            # Anything else
            msg = MIMEMultipart()
            alternative = MIMEMultipart('alternative')
            alternative.attach(self._mimetext(self.body, 'plain'))
            alternative.attach(self._mimetext(self.html, 'html'))
            msg.attach(alternative)

        if self.subject:
            msg['Subject'] = sanitize_subject(force_text(self.subject), encoding)

        msg['From'] = sanitize_address(self.sender, encoding)
        msg['To'] = ', '.join(list(set(sanitize_addresses(self.recipients, encoding))))

        msg['Date'] = formatdate(self.date, localtime=True)
        # see RFC 5322 section 3.6.4.
        msg['Message-ID'] = self.msgId
        
        # import pdb; pdb.set_trace()

        if self.cc:
            msg['Cc'] = ', '.join(list(set(sanitize_addresses(self.cc, encoding))))
            
        if self.reply_to:
            msg['Reply-To'] = sanitize_address(self.reply_to, encoding)

        if self.extra_headers:
            for k, v in self.extra_headers.items():
                msg[k] = v

        SPACES = re.compile(r'[\s]+', re.UNICODE)
        for attachment in attachments:
            f = MIMEBase(*attachment.content_type.split('/'))
            f.set_payload(attachment.data)
            encode_base64(f)

            filename = attachment.filename
            if filename and ascii_attachments:
                # force filename to ascii
                filename = unicodedata.normalize('NFKD', filename)
                filename = filename.encode('ascii', 'ignore').decode('ascii')
                filename = SPACES.sub(u' ', filename).strip()

            try:
                filename and filename.encode('ascii')
            except UnicodeEncodeError:
                if not PY3:
                    filename = filename.encode('utf8')
                filename = ('UTF8', '', filename)

            f.add_header('Content-Disposition',
                         attachment.disposition,
                         filename=filename)

            for key, value in attachment.headers:
                f.add_header(key, value)

            msg.attach(f)
        if message_policy:
            msg.policy = message_policy

        return msg

    def as_string(self):
        return self._message().as_string()

    def as_bytes(self):
        if PY34:
            return self._message().as_bytes()
        else: # fallback for old Python (3) versions
            return self._message().as_string().encode(self.charset or 'utf-8')

    def __str__(self):
        return self.as_string()

    def __bytes__(self):
        return self.as_bytes()

    def has_bad_headers(self):
        """Checks for bad headers i.e. newlines in subject, sender or recipients.
        RFC5322: Allows multiline CRLF with trailing whitespace (FWS) in headers
        """

        headers = [self.sender, self.reply_to] + self.recipients
        for header in headers:
            if _has_newline(header):
                return True

        if self.subject:
            if _has_newline(self.subject):
                for linenum, line in enumerate(self.subject.split('\r\n')):
                    if not line:
                        return True
                    if linenum > 0 and line[0] not in '\t ':
                        return True
                    if _has_newline(line):
                        return True
                    if len(line.strip()) == 0:
                        return True
        return False

    def add_recipient(self, recipient):
        """Adds another recipient to the message.

        :param recipient: email address of recipient.
        """

        self.recipients.append(recipient)

    def attach(self,
               filename=None,
               content_type=None,
               data=None,
               disposition=None,
               headers=None):
        """Adds an attachment to the message.

        :param filename: filename of attachment
        :param content_type: file mimetype
        :param data: the raw file data
        :param disposition: content-disposition (if any)
        """
        self.attachments.append(
            Attachment(filename, content_type, data, disposition, headers))
            
            
class GmailAPIMessage(Message):
    """A subclass of Message for messages to be sent using the gmail API
    
    Args: Same as Message
    
    Returns: None
    
    """
    
    def send(self, mail):
        """Send the message dirctly to google using the API
        
        Args:
            mail: an instance of Mail initialized for this message
            
        """
        
        service = self.get_credentials()
        
        # The next line will add all cc and bcc addresses to the email
        # At the moment they all seem to end up in the To headers so bcc doesnt really work as expected
        # self.recipients = self.send_to
        
        if mail.suppress:
            #just testing
            return self # you could inspect the message in a test
            
        return service.users().messages().send(
          userId="me",
          body={'raw': urlsafe_b64encode(self.as_bytes()).decode()}
        ).execute()
        
        
    def get_credentials(self):
        """
        
        Load the API credentials and return the service discovery object instance
        
        Args: None
        
        Returns: googleapiclient.discovery instance
            
        Raises:
            MailSettingsError
        """
        
        TOKEN_FILE_PATH = get_site_config().get('MAIL_TOKEN_PATH','')
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        # set_trace()
        try:
            with open(TOKEN_FILE_PATH, "rb") as token:
                creds = pickle.load(token)
        except FileNotFoundError:
            raise MailSettingsError("Gmail API token file not found.")
        # if there are no (valid) credentials availablle stop here.
        if not creds:
            raise MailSettingsError("Gmail API credentials are missing.")
            
        if creds.expired: # and creds.refresh_token:
            creds.refresh(Request())
            # save the credentials for the next run
            with open(TOKEN_FILE_PATH, "wb") as token:
                pickle.dump(creds, token)
        try:
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            raise MailSettingsError("Gmail API could not build a connection. Err: {}".format(str(e)))
    
