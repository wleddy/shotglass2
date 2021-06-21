"""Generate a file containing a pickled gmail authentication object

Adapted from: https://www.thepythoncode.com/article/use-gmail-api-in-python

This will walk through the process of creating a gmail oAuth credentials object
and store it in a pickle file.

Once you have the pickle file you can move it to the web server machine and point your
settings to it.

The files used by and created here contain confidential information and
should not be committed to the repo.

"""

import os
import pickle
from pdb import set_trace
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

import webbrowser

# Gmail API utils
try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("You seem to be missing some required packages.")
    print("run the following to add them to your virtual env.")
    print()
    print("pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    print()
    exit()
    
# from flow import InstalledAppFlow


# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
_OOB_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time

    if os.path.exists(PICKLE_FILE_PATH):
        with open(PICKLE_FILE_PATH, "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            # creds = flow.run_local_server(port=0)
            
            flow.redirect_uri=_OOB_REDIRECT_URI
            auth_url, _ = flow.authorization_url()
            
            webbrowser.open(auth_url, new=1, autoraise=True)

            creds = flow.run_console(authorization_prompt_message='Auth URL: {url}')
            # creds = flow.run_local_server(port=8080)
        # save the credentials for the next run
        with open(PICKLE_FILE_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# Adds the attachment with the given filename to the given message
def add_attachment(message, filename):
    content_type, encoding = guess_mime_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    try:
        with open(filename,'rb') as fp:
            if main_type == 'text':
                msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            elif main_type == 'image':
                msg = MIMEImage(fp.read(), _subtype=sub_type)
            elif main_type == 'audio':
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
            else:
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())
            
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)
        
    except FileNotFoundError:
        pass


def _mimetext(text, subtype='plain'):
    """Creates a MIMEText object with the given subtype (default: 'plain')
    If the text is unicode, the utf-8 charset is used.
    """
    # charset = self.charset or 'utf-8'
    return MIMEText(text, _subtype=subtype, _charset='utf-8')


def build_message(destination, subject, body, html=None, attachments=[]):
    if not attachments and not html: # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = ACCOUNT_EMAIL_ADDRESS
        message['subject'] = subject
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = ACCOUNT_EMAIL_ADDRESS
        message['subject'] = subject
        if html:
            alternative = MIMEMultipart('alternative')
            alternative.attach(_mimetext(body, 'plain'))
            alternative.attach(_mimetext(html, 'html'))
            message.attach(alternative)
        else:
            message.attach(MIMEText(body))
            
        for filename in attachments:
            add_attachment(message, filename)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}
    
    
def send_message(destination, subject, body, html=None, attachments=[]):
    # get the Gmail API service
    service = gmail_authenticate()
    
    return service.users().messages().send(
      userId="me",
      body=build_message(destination, subject, body, html, attachments)
    ).execute()
    
    
def get_input(prompt):
    """Return an input string or exit"""

    response = None

    while not response:
        response = input(prompt + " ('q' to exit): ").strip()
    
    if response.lower() == 'q':
        exit()
    
    return response
    
    
if __name__ == '__main__':
    print("""
Welcome to the show

This tool will create the gmail oAuth credentials and store them in a pickled file.

For background details got to https://www.thepythoncode.com/article/use-gmail-api-in-python#Enabling_Gmail_API

You will need to download the credentials for your gmail api project. 
Go to https://console.developers.google.com to set up your api and download your credentials
*** Also, very important that you ENABLE the api at the same time. ***
""")
    ACCOUNT_EMAIL_ADDRESS = get_input("Enter the email address for the credntials")
    valid_path = False
    while not valid_path:
        CREDENTIALS_PATH = get_input("Enter path to the credentials download")
        if not os.path.exists(CREDENTIALS_PATH):
            print("*** file not found ***")
        else:
            valid_path = True
            
    PICKLE_FILE_PATH = get_input("Enter the path to the output file")
    
    print()
    print("Ready to create credentials. If you answer Y to the next prompt your web browser will open")
    print("Follow the prompts to receive the authorisation code and paste it below")
    proceed = get_input("Create Credentioals? Y/N")
    if proceed[0:1].lower()=="y":
        gmail_authenticate()
        print("Creating pickle file")
        print("Credentials saved at {}".format(PICKLE_FILE_PATH))
        print()
    
        proceed = get_input("Send test Email? Y/N")
        if proceed.lower()=="y":
            TO_EMAIL_ADDRESS = get_input("Enter TO email address")
            # test send email
            send_message(TO_EMAIL_ADDRESS, "This is a subject",
                        "This is the body of the email", html='<h1>Greetings!</h1><p>This is the body of the email in html</p>')

            print("email sent")
        else:
            print("no email sent")
    else:
        print("Credentials not created")


