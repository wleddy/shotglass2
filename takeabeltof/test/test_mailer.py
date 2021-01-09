import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import pytest
#with pytest.raises(Exception):

from app import app
app.config['TESTING'] = True

# try:
#     from flask_mail import Mail
#     with app.app_context():
#         # need to recreate mail obj to get new TESTING value
#         from app import mail
#         del mail
#         mail = Mail(app)
# except:
#     pass

import shotglass2.takeabeltof.mailer as mail

def test_send_message():
    with app.app_context():
        success, mes = mail.send_message([("Bill Leddy",'bill@example.com')],body="This is a test",subject="Simple Test")
        assert success == True
        assert "sent successfully" in mes
    
        # try sending with the name and addres in the wrong order
        success, mes = mail.send_message([('bill@example.com',"Bill Leddy")],body="This is a test with name and address params reversed",subject="Reversed address Test")
        assert success == True
        assert "sent successfully" in mes

        # try address only
        success, mes = mail.send_message(["bill@computer.com"],body="Address only test test",subject="Address Test")
        assert success == True
        assert "sent successfully" in mes

        #try sending to a group
        success, mes = mail.send_message([("bill Leddy",'bill@example.com'),('bill@computer.com')],body="This is a group email",subject="Group Email")
        assert success == True
        assert "sent successfully" in mes
        
        success, mes = mail.send_message()
        assert success == False
        assert mes == "Message contained no body content."
        
def test_construct_mail_class():
    with app.app_context():
        mailer = mail.Mailer()
        assert isinstance(mailer,mail.Mailer)
        
        mailer.add_address('bill@example.net')
        assert mailer._to == [('bill@example.net','bill@example.net')]
        mailer.add_address(('Joe Banana','joe@the_bunch.bunch'))
        assert mailer._to == [('bill@example.net','bill@example.net'),('Joe Banana','joe@the_bunch.bunch')]
        mailer.add_address([('willie','willy@willie.net'),('smithy','smithy@willie.net'),])
        assert mailer._to == [('bill@example.net','bill@example.net'),('Joe Banana','joe@the_bunch.bunch'),('willie','willy@willie.net'),('smithy','smithy@willie.net')]
        mailer.add_address([('nilly@willie.net')])
        assert mailer._to == [('bill@example.net','bill@example.net'),('Joe Banana','joe@the_bunch.bunch'),('willie','willy@willie.net'),('smithy','smithy@willie.net'),('nilly@willie.net','nilly@willie.net')]
            
        mailer.add_cc('bill@example.net')
        assert mailer._cc == ['bill@example.net']
        mailer.add_cc(('Joe Banana','joe@the_bunch.bunch'))
        assert mailer._cc == ['bill@example.net','joe@the_bunch.bunch']
        mailer.add_cc([('willie','willy@willie.net'),('smithy','smithy@willie.net'),])
        assert mailer._cc == ['bill@example.net','joe@the_bunch.bunch','willy@willie.net','smithy@willie.net']
        mailer.add_cc([('nilly@willie.net')])
        assert mailer._cc == ['bill@example.net','joe@the_bunch.bunch','willy@willie.net','smithy@willie.net','nilly@willie.net']

        mailer.add_bcc('bill@example.net')
        assert mailer._bcc == ['bill@example.net']
        mailer.add_bcc(('Joe Banana','joe@the_bunch.bunch'))
        assert mailer._bcc == ['bill@example.net','joe@the_bunch.bunch']
        mailer.add_bcc([('willie','willy@willie.net'),('smithy','smithy@willie.net'),])
        assert mailer._bcc == ['bill@example.net','joe@the_bunch.bunch','willy@willie.net','smithy@willie.net']
        mailer.add_bcc([('nilly@willie.net')])
        assert mailer._bcc == ['bill@example.net','joe@the_bunch.bunch','willy@willie.net','smithy@willie.net','nilly@willie.net']
            
        mailer.subject = 'test'
        mailer.body = "test"
        
        mailer.send()
        assert mailer.success == True
        assert 'sent successfully' in mailer.result_text
                
def test_attachments():
    with app.app_context():
        mailer = mail.Mailer("bill@example.net",attachment=('Myfile.txt','text/plain','Hello World'))
        assert isinstance(mailer._attachments,list)
        assert len(mailer._attachments) == 1
        assert len(mailer._attachments[0]) == 3
        
        mailer.add_attachments([('Myfile.txt','text/plain','Hello World'),('Myfile.txt','text/plain','Hello World'),('Myfile.txt','text/plain','Hello World')])
        assert len(mailer._attachments) == 4
        
        mailer.add_attachment('not a tuple')
        mailer.add_attachment(('too short'))
        mailer.add_attachment(('too long','now is the time','for all good men','to take a break'))
        mailer.add_attachment(['still not a tuple'])
        assert len(mailer._attachments) == 4
        
                    
def test_alert_admin():
    with app.app_context():
        success, mes = mail.alert_admin("Error Subject","There was really no error, just testing")
        assert success == True
        assert "sent successfully" in mes
        
        #Calling with no params should not cause an error
        success, mes = mail.alert_admin()
        assert success == True
        assert "sent successfully" in mes

# tests sending mail with google oAuth credentials
def test_send_googl_message():
    with app.app_context():
        success, mes = mail.send_message([("Bill Leddy",'williesworkshop.net@gmail.com')],body="This is a test",subject="Simple Test")
        assert success == True
        assert "sent successfully" in mes
