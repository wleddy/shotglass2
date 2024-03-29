
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app
from shotglass2.users.views.password import getPasswordHash

def abs_path(file):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),file)
        

@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE_PATH'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()
           
    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE_PATH'])
    
    
filespec = 'instance/test_roles.db'
db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.initalize_base_tables(db)

        
def delete_test_db():
        os.remove(filespec)

    
def test_create_test_data():
    # Populate the test database
    from shotglass2.users.models import User
    try:
        f = open( abs_path('test_data_create.sql'),'r')
        sql = f.read()
        f.close()
        cur = db.cursor()
        cur.executescript(sql)

        rec = User(db).get('doris')
        rec.password = getPasswordHash('password')
        User(db).save(rec)
        rec = User(db).get('John')
        rec.password = getPasswordHash('password')
        User(db).save(rec)
        db.commit()

        assert True == True

    except:
        assert True == False
            
            
def test_roles():
    from shotglass2.users.models import Role
    #db = get_test_db()
    
    assert Role(db).get(0) == None 
    
    recs = Role(db).select()
    assert recs != None
    assert len(recs)==3
    assert recs[0].name != None
    
    rec = Role(db).new()
    rec.name = "Testing"
    rec.description = "A test role"
    
    recID = Role(db).save(rec)
    rec = Role(db).get(recID)
    assert rec.id == recID
    assert rec.name == 'Testing'
    assert rec.rank == 0
    
    # test get by role name
    rec = Role(db).get('Testing')
    assert rec.id == recID

    # test that bad name is not found
    none_rec = Role(db).get('Wrong name')
    assert none_rec == None
    
    #Modify the record
    rec.name = "New Test"
    rec.rank = 300
    Role(db).save(rec)
    rec = Role(db).get(rec.id)
    assert rec.name == "New Test"
    assert rec.rank == 300
    
    db.rollback()
    
def nogood_test_list_page(client):
    """Right now this fails missurably, but when it was 'working' it was operating on the live database instead
    of the temporary one like the docs implied it would."""
    with app.app.app_context():
        with client as c:
            from flask import session, g
            from shotglass2.users.models import User,Role
            import app
            print(app.app.config['DATABASE_PATH'])
            app.get_db(app.app.config['DATABASE_PATH'])
            # access without login
            result = c.get('/user/delete/3/',follow_redirects=True)  
            assert result.status_code == 200
            assert b'Sorry. You do not have access to that page' in result.data
        
            rec = User(app.g.db).get('John')
            print(rec)
        
            # Login as user role
            result = c.post('/login/', data={'userNameOrEmail': 'John', 'password': 'password'},follow_redirects=True)
            assert result.status == '200 OK'
            assert b'Invalid User Name or Password' not in result.data
            assert session['user'] == 'John'
        
            #attempt to delete a record
            result = c.get('/role/delete/3/',follow_redirects=True)  
            assert result.status_code == 200
            assert b'Sorry. You do not have access to that page' in result.data
    
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert True
