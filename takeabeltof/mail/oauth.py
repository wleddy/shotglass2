""" Handle sending mail using oAuth authentication

A tool to collect the needed credentials to connect to a gmail account for the
purpose of sending (and possibly receiving) mail through their server.

This is a lightly edited version of a script creatd by Seppe "Macuyiko" vanden Broucke
on his/her/their blog 'Bed Against The Wall' at 
https://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html
Unless mentioned otherwise, this work is licensed under a Creative Commons Attribution-Share 
Alike 2.0 Belgium License (http://creativecommons.org/licenses/by-sa/2.0/be/).

Adapted from:
https://github.com/google/gmail-oauth2-tools/blob/master/python/oauth2.py
https://developers.google.com/identity/protocols/OAuth2

1. Generate and authorize an OAuth2 (generate_oauth2_token)
2. Generate a new access tokens using a refresh token(refresh_token)
3. Generate an OAuth2 string to use for login (access_token)

Args: None

Returns:  None

Raises: None
"""

import base64
import json
import smtplib
import urllib.parse
import urllib.request


def call_refresh_token(client_id, client_secret, refresh_token, token_request_url):
    # Used here
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    # request_url = command_to_url('o/oauth2/token')
    request_url = '%s/%s' % (token_request_url, 'o/oauth2/token')
    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('UTF-8')).read().decode('UTF-8')
        
    return json.loads(response)


def generate_oauth2_string(username, access_token, as_base64=False):
    #used here
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


def refresh_authorization(client_id, client_secret, refresh_token, token_request_url):
    # Used here
    #from call_refesh_token
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    # request_url = command_to_url('o/oauth2/token')
    request_url = '%s/%s' % (token_request_url, 'o/oauth2/token')

    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('UTF-8')).read().decode('UTF-8')
    response = json.loads(response)  
    # return json.loads(response)

    # response = call_refresh_token(client_id, client_secret, refresh_token)
    return response['access_token'], response['expires_in']


def get_host_connection(mail):
    """Connect to oAuth host and return connection object
    
    Args: mail.Mail() instance
    
    Returns: 
        smtplib.SMTP() instance representing a connection to the mail server
    
    Raises: None
    """
    
    # import pdb;pdb.set_trace()
    
    access_token, expires_in = refresh_authorization(mail.client_id, mail.client_secret, mail.refresh_token,mail.token_request_url)
    auth_string = generate_oauth2_string(mail.username, access_token, as_base64=True)
    
    host = smtplib.SMTP(mail.server,mail.port)
    host.set_debuglevel(int(mail.debug))
    host.ehlo(mail.client_id)
    host.starttls()
    host.docmd('AUTH', 'XOAUTH2 ' + auth_string)
    
    return host

