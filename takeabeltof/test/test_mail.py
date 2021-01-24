import sys
#print(sys.path)
# sys.path.append('') ##get import to look in the working dir.
from dataclasses import dataclass, field
import os
import pickle
from pdb import set_trace
import pytest
#with pytest.raises(Exception):

from flask import g
from app import app

from shotglass2.takeabeltof.mail import mail

test_token_path = os.path.join(os.path.dirname(__file__),'gmail_dummy_token.pickle')
class DummyCredentials:
    "A simple class to help test the Gmail API message creation"
    
    expired = False
    just_testing = True
    
    
creds = DummyCredentials()
with open(test_token_path, "wb") as token:
    pickle.dump(creds, token)

@pytest.fixture
def m():
    with app.app_context():
        app.config['TESTING'] = True
        app.config['MAIL_SERVER'] = 'mail.example.com'
        app.config['MAIL_USERNAME'] = "some_mail_user"
        app.config['MAIL_PASSWORD'] = "some_password"
        app.config['MAIL_DEFAULT_SENDER'] = "Some Body"
        app.config['MAIL_DEFAULT_ADDR'] = 'somebody@example.com'
        
        # set_trace()
        return mail.Mail()
        
        
class ClassicMessage:
    def __init__(self,m):
        self.sender = (m.default_sender_name,m.default_sender_addr,)
        self.subject = 'subject'
        self.recipients = [('joe banana','joe@thebunch.com'),'jaine@doe.com',]
        self.body = "This is a test"
        self.html = '<p>Hello World</p>'
        
class GmailMessage:
    pass
    
@pytest.fixture
def mes(m):
    d = ClassicMessage(m)
    mes = mail.Message(
        subject = d.subject,
        recipients = d.recipients,
        sender = d.sender,
        body = d.body,
        html = d.html,
        )
    return mes
    
@pytest.fixture
def gmes(m):
    d = ClassicMessage(m)
    mes = mail.GmailAPIMessage(
        subject = d.subject,
        recipients = d.recipients,
        sender = d.sender,
        body = d.body,
        html = d.html,
        token_file_path = test_token_path,
    )
    
    return mes
    
    
def test_mail_class(m):
    assert isinstance(m,mail.Mail)
    assert m.server == 'mail.example.com'
    assert m.username == 'some_mail_user'
    assert m.password == 'some_password'
    assert m.port is not None
    assert m.default_sender_name == 'Some Body'
    assert m.default_sender_addr == 'somebody@example.com'
    assert m.suppress == True
    
    
def test_mail_send(m,mes):
    mes = m.send(mes)
    assert mes
        
        
def test_create_message(m,mes):
    assert isinstance(mes,mail.Message)
    assert not isinstance(mes,mail.GmailAPIMessage)
    assert mes.sender == f"{m.default_sender_name} <{m.default_sender_addr}>"
    assert len(mes.recipients) == 2
    assert len(mes.attachments) == 0
    assert len(mes.body) > 0
    id = mes.msgId
    assert id
    assert isinstance(id,str)
    mstr = mes.as_string()
    assert mstr
    assert isinstance(mstr,str)
    for r in mes.recipients:
        if isinstance(r,tuple):
            assert r[1] in mstr
        else:
            assert r in mstr
    assert mes.body in mstr
    assert mes.html in mstr
    assert mes.send_to == set(mes.recipients)
    
    
def test_message_attachment(mes):
    d = dict(filename='my_file.txt',content_type='text/plain',data="Now is the time",
        disposition='octet-stream',headers={'platform':'Any'},)
    mes.attach(**d)
    assert len(mes.attachments) == 1
    assert isinstance(mes.attachments[0],mail.Attachment)
    
    
def test_add_recipient(mes):
    mes.add_recipient('sonny@skies.com')
    mes.add_recipient(('char','char@skies.com',))
    assert len(mes.send_to) == 4
    
    
def test_message_has_bad_headers(mes):
    assert not mes.has_bad_headers()
    mes.subject = mes.subject + '\r\r'
    assert mes.has_bad_headers()
    
    
def test_message_as_bytes(mes):
    assert isinstance(mes.as_bytes(),bytes)
        
        
def test_message_as_string(mes):
    assert isinstance(mes.as_string(),str)
    
    
def test_Gmail_api(m,gmes):
    assert gmes.token_file_path == test_token_path
    assert isinstance(gmes,mail.GmailAPIMessage)
    assert gmes.sender == f"{m.default_sender_name} <{m.default_sender_addr}>"
    assert len(gmes.recipients) == 2
    assert len(gmes.attachments) == 0
    assert len(gmes.body) > 0
    
    cred = gmes.get_credentials()
    assert cred.just_testing
    

def test_pickle_file_missing(m,gmes):
    assert isinstance(gmes,mail.GmailAPIMessage)
    gmes.token_file_path = 'notarealpath'
    with pytest.raises(mail.MailSettingsError):
        cred = gmes.get_credentials() # should raise exception
    
    
def test_sanitize_address():
    l = ['sonny@skies.com',('char','char@skies.com',)]
    addr = mail.sanitize_address(l[0])
    assert addr == l[0]
    addr = mail.sanitize_address(l[1])
    assert addr == '=?utf-8?q?char?= <char@skies.com>'
    
    
def test_sanitize_subject():
    subject = "How Are You"
    assert mail.sanitize_subject(subject) == subject
    subject = subject + '\r\nNot too bad.'
    assert mail.sanitize_subject(subject) == subject
    
    
def test_attachment():
    d = dict(filename='my_file.txt',content_type='text/plain',data="Now is the time",
        disposition='octet-stream',headers={'platform':'Any'},)
    a = mail.Attachment(**d)
    assert isinstance(a,mail.Attachment)
    assert a.filename == d['filename']
    assert a.content_type == d['content_type']
    assert a.data == d['data']
    assert a.disposition == d['disposition']
    assert a.headers == d['headers']
    
    
def test_connection(m):
    # not at all sure how to test this since it wants to connect to a server...
    pass
    
    
# delete the test pickle
def test_delete_pickle():
    if os.path.exists(test_token_path):
        os.remove(test_token_path)
    assert not os.path.exists(test_token_path)

