
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app
from shotglass2.users.views.password import getPasswordHash

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
    app.init_db(db)

        
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
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert True
