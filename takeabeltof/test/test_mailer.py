import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import pytest
#with pytest.raises(Exception):

from app import app
app.config['TESTING'] = True

try:
    from flask_mail import Mail
    with app.app_context():
        # need to recreate mail obj to get new TESTING value
        from app import mail
        del mail
        mail = Mail(app)
except:
    pass

import shotglass2.takeabeltof.mailer as mail

def test_send_message():
    with app.app_context():
        success, mes = mail.send_message([("Bill Leddy",'bill@williesworkshop.com')],body="This is a test",subject="Simple Test")
        assert success == True
        assert "sent successfully" in mes
    
        # try sending with the name and addres in the wrong order
        success, mes = mail.send_message([('bill@williesworkshop.com',"Bill Leddy")],body="This is a test with name and address params reversed",subject="Reversed address Test")
        assert success == True
        assert "sent successfully" in mes

        # try address only
        success, mes = mail.send_message(["bill@leddyconsulting.com"],body="Address only test test",subject="Address Test")
        assert success == True
        assert "sent successfully" in mes

        #try sending to a group
        success, mes = mail.send_message([("bill Leddy",'bill@williesworkshop.com'),('bill@leddyconsulting.com')],body="This is a group email",subject="Group Email")
        assert success == True
        assert "sent successfully" in mes
        
        success, mes = mail.send_message()
        assert success == False
        assert mes == "No message body was specified"
        
    

def test_alert_admin():
    with app.app_context():
        success, mes = mail.alert_admin("Error Subject","There was really no error, just testing")
        assert success == True
        assert "sent successfully" in mes
        
        #Calling with no params should not cause an error
        success, mes = mail.alert_admin()
        assert success == True
        assert "sent successfully" in mes
