""" Generates an access token for gmail authentication

Run the script to generate an authentication token that
can be used to send mail through the gmail servers

Option to send a test email as well

This is an edited version of a script creatd by Seppe "Macuyiko" vanden Broucke
on his/her/their blog 'Bed Against The Wall' at 
https://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html
Unless mentioned otherwise, this work is licensed under a Creative Commons Attribution-Share 
Alike 2.0 Belgium License (http://creativecommons.org/licenses/by-sa/2.0/be/).


See the README.md file for more info.

"""

import base64
import imaplib
import json
import smtplib
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# --- lxml.html is used to strip out the html tags from the EMAIL_BODY
# --- It must be added to the vend via pip install lsml
# --- I did not find it useful for this script, so I left it out
# --- If you want it, be sure to uncomment the plain text part in send_email
# import lxml.html

GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
EMAIL_SUBJECT = 'A mail from you from Python'
EMAIL_BODY = '<b>A mail from you from Python</b><br><br>So happy to hear from you!'

def command_to_url(command):
    return '%s/%s' % (GOOGLE_ACCOUNTS_BASE_URL, command)


def url_escape(text):
    return urllib.parse.quote(text, safe='~-._')


def url_unescape(text):
    return urllib.parse.unquote(text)


def url_format_params(params):
    param_fragments = []
    for param in sorted(params.items(), key=lambda x: x[0]):
        param_fragments.append('%s=%s' % (param[0], url_escape(param[1])))
    return '&'.join(param_fragments)


def generate_permission_url(client_id, scope='https://mail.google.com/'):
    params = {}
    params['client_id'] = client_id
    params['redirect_uri'] = REDIRECT_URI
    params['scope'] = scope
    params['response_type'] = 'code'
    return '%s?%s' % (command_to_url('o/oauth2/auth'), url_format_params(params))


def call_authorize_tokens(client_id, client_secret, authorization_code):
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['code'] = authorization_code
    params['redirect_uri'] = REDIRECT_URI
    params['grant_type'] = 'authorization_code'
    request_url = command_to_url('o/oauth2/token')
    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('UTF-8')).read().decode('UTF-8')
    return json.loads(response)


def call_refresh_token(client_id, client_secret, refresh_token):
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    request_url = command_to_url('o/oauth2/token')
    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('UTF-8')).read().decode('UTF-8')
        
    return json.loads(response)


def generate_oauth2_string(username, access_token, as_base64=False):
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


def test_imap(user, auth_string):
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
    imap_conn.debug = 4
    imap_conn.authenticate('XOAUTH2', lambda x: auth_string)
    imap_conn.select('INBOX')


def test_smpt(user, base64_auth_string):
    smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_conn.set_debuglevel(True)
    smtp_conn.ehlo('test')
    smtp_conn.starttls()
    smtp_conn.docmd('AUTH', 'XOAUTH2 ' + base64_auth_string)


def get_authorization(google_client_id, google_client_secret):
    scope = "https://mail.google.com/"
    print()
    print('Navigate to the following URL to auth:')
    print()
    print(generate_permission_url(google_client_id, scope))
    print()
    authorization_code = get_input('Enter verification code')
    response = call_authorize_tokens(google_client_id, google_client_secret, authorization_code)
    return response['refresh_token'], response['access_token'], response['expires_in']


def refresh_authorization(google_client_id, google_client_secret, refresh_token):
    response = call_refresh_token(google_client_id, google_client_secret, refresh_token)
    return response['access_token'], response['expires_in']


def send_mail(fromaddr, toaddr, subject, message):
    access_token, expires_in = refresh_authorization(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN)
    auth_string = generate_oauth2_string(fromaddr, access_token, as_base64=True)

    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg.preamble = 'This is a multi-part message in MIME format.'
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    part_html = MIMEText(message.encode('utf-8'), 'html', _charset='utf-8')
    msg_alternative.attach(part_html)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo(GOOGLE_CLIENT_ID)
    server.starttls()
    server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()

def get_input(prompt):
    """Return an input string or exit"""
    
    response = None
    
    while not response:
        response = input(prompt + " ('q' to exit): ")
        
    if response.lower() == 'q':
        exit()
        
    return response

if __name__ == '__main__':
    GOOGLE_CLIENT_ID = get_input("Enter Client ID")
    GOOGLE_CLIENT_SECRET = get_input("Enter Client Secret")
    GOOGLE_REFRESH_TOKEN, access_token, expires_in = get_authorization(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
    print("")
    print("*******")
    print("Refresh Token: {}".format(GOOGLE_REFRESH_TOKEN))
    print("*******")
    print("")
    proceed = get_input("Send test Email? Y/N")
    if proceed.lower()=="y":
        FROM_EMAIL_ADDRESS = get_input("Enter FROM email address")
        TO_EMAIL_ADDRESS = get_input("Enter TO email address")
        send_mail(FROM_EMAIL_ADDRESS, TO_EMAIL_ADDRESS,
                  EMAIL_SUBJECT,
                  EMAIL_BODY)
                  
        print("email sent")
        