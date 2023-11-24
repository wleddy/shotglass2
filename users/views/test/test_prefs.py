
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

from flask import g

import app
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString

@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE_PATH'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()

        
    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE_PATH'])
    
    
filespec = 'instance/test_prefs.db'
db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.initalize_base_tables(db)

        
def delete_test_db():
        os.remove(filespec)

    
def test_prefs():
    from shotglass2.users.models import Pref
    #db = get_test_db()
    
    assert Pref(db).get(0) == None 
    assert Pref(db).get("this") == None 
        
    rec = Pref(db).new()
    rec.name = "Testing"
    rec.value = "A test value"
    
    recID = Pref(db).save(rec)
    rec = Pref(db).get(recID)
    assert rec.id == recID
    assert rec.name == 'Testing'
    assert rec.value == "A test value"
    
    rec = Pref(db).get('Testing')
    assert rec.name == 'Testing'
    assert rec.value == "A test value"

    # get is now case in-sensitive
    rec = Pref(db).get('testing')
    assert rec.name == 'Testing'
    assert rec.value == "A test value"

    #Modify the record
    rec.name = "New Test"
    Pref(db).save(rec)
    rec = Pref(db).get(rec.id)
    assert rec.name == "New Test"
    
    db.rollback()
    
    # test the default setting
    pref_name = "A new pref"
    default_value = "A Default value"
    rec = Pref(db).get(pref_name)
    assert rec == None
    
    # create a new record with default values
    rec = Pref(db).get(pref_name,default=default_value)
    assert rec != None
    assert rec.name == pref_name
    assert rec.value == default_value
    assert rec.user_name == None
    
    # create another except has a user name
    rec = Pref(db).get(pref_name,user_name='test',default="new value")
    assert rec != None
    assert rec.name == pref_name
    assert rec.value == 'new value'
    assert rec.user_name == 'test'
    
    # get the generic record
    rec = Pref(db).get(pref_name)
    assert rec != None
    assert rec.name == pref_name
    assert rec.value == default_value
    
    # get the user specific record. Providing a default should not change the record
    rec = Pref(db).get(pref_name,user_name='test',default="someother value")
    assert rec != None
    assert rec.name == pref_name
    assert rec.value == 'new value'
    assert rec.user_name == 'test'
    
    # this should have no effect because get with default does a commit
    db.rollback()
    
    rec = Pref(db).get(pref_name)
    assert rec != None
    assert rec.name == pref_name
    assert rec.value == default_value
    
    
    #new pref was committed, so delete it
    assert Pref(db).delete(rec.id) == True
    db.commit()
    
    #Test that it's really gone
    rec = Pref(db).get(pref_name)
    assert rec == None
    
    # make with all values
    temp_date = local_datetime_now()
    
    pref = Pref(db)
    rec = pref.get("sample1",default="me",description="test me",user_name='willie',expires=temp_date)
    assert rec != None
    assert rec.name == "sample1"
    assert rec.value == "me"
    assert rec.description == "test me"
    assert rec.user_name == "willie"
    assert getDatetimeFromString(rec.expires).date() == temp_date.date()
    
    
def test_get_contact_email():
    from shotglass2.users.models import Pref
    from shotglass2.users.views import pref
    with app.app.app_context():
        app.app.config['TESTING'] = True
        # import pdb;pdb.set_trace()
        g.db = db
        val = 'willie@example.com'
        user = 'test'
        rec = Pref(g.db).get('Contact Email Address',user_name=user,default=val)
        rec.value = val
        rec.user_name = user
        Pref(g.db).save(rec)
        db.commit()
        contact = pref.get_contact_email()
        assert isinstance(contact,tuple)
        assert contact[1] == val
        
        # test that list is returned for multiple addresses
        val = 'willie@example.com,mcgilly@example.com'
        rec = Pref(g.db).get('Contact Email Address',user_name=user)
        rec.value = val
        Pref(g.db).save(rec)
        db.commit()
        contact = pref.get_contact_email()
        assert isinstance(contact,list)
        assert contact[0][1] == val.split(',')[0]
        assert contact[1][1] == val.split(',')[1]
        
        
    
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert True
