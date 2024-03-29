import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app


@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE_PATH'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        print(app.app.config['DATABASE_PATH'])
        app.initalize_base_tables(app.get_db(app.app.config['DATABASE_PATH'])) 
        print(app.g.db)
        
    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE_PATH'])
    
    
filespec = 'instance/test_users.db'

db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.initalize_base_tables(db)

        
def delete_test_db():
        os.remove(filespec)
        
def abs_path(file):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)),file)
        
def test_create_test_data():
    # Populate the test database
    try:
        #f = open('shotglass2/users/views/test/test_data_create.sql','r')
        f = open( abs_path('test_data_create.sql'),'r')
        sql = f.read()
        f.close()
        cur = db.cursor()
        cur.executescript(sql)
        
        assert cur != None
        
    except:
        assert True == False
    
    
    
def test_user_get():
    from shotglass2.users.models import User

    #do some tests...
    user = User(db)
    rec = user.get(1)
    assert rec.username == 'admin'
    rec = user.get('admin')
    assert rec.username == 'admin'
    
    admin_roles = user.get_roles(rec.id)
    assert admin_roles != None
    assert len(admin_roles)>0
    assert admin_roles[0].name == "super"
    
    assert user.max_role_rank(1) == 1000;
    assert user.max_role_rank('admin') == 1000;
    
    # test that user admin is in admins
    assert user.is_admin('admin')
    assert user.is_admin(rec.id)
    
    #user John is not administrator
    rec = user.get('John')
    assert user.is_admin(rec.id) == False
        
    recs = user.select()
    assert len(recs) == 3
    # select inactive users too...
    recs = user.select(include_inactive=True)
    assert len(recs) == 4
    #ensure that inactive users are not returned with get
    rec = user.get('none') # search on username
    assert rec == None
    #and now we can...
    rec = user.get('none',include_inactive=True)
    assert rec.username == 'none'
    
    # user 'none' has no roles
    assert user.get_roles(rec.id) == None
    
    #add some roles for none
    user.add_role(rec.id,'user')
    assert user.get_roles(rec.id) != None
    
    #ensure that username is case sensitive
    rec = user.get('doris')
    assert rec.username == 'doris'
    rec = user.get('Doris')
    assert rec == None
    #get by email and NOT case sensitive
    rec = user.get('John@example.com')
    assert rec.last_name == "Goodman"
    rec = user.get('john@example.com')
    assert rec.last_name == "Goodman"
    #and that spaces are stripped
    rec = user.get(' john@example.com ')
    assert rec.last_name == "Goodman"
    #test a total miss
    assert user.get('something that doesnt exist') == None
    assert user.get(234343) == None
    
def test_user_creation():
    from shotglass2.users.models import User
    #create some user records
    user = User(db)
    
    rec = user.new()
    assert rec != None
    rec.first_name = 'Another'
    rec.last_name = 'User'
    rec.username = ' anotheruser ' # Spaces should be trimmed
    rec.email = 'anotheruser@example.com'
    new_id = user.save(rec)
    assert new_id != None
    assert new_id > 0
    assert rec.active == 1 #test the default value
    assert rec.username == 'anotheruser'
    
    db.rollback()
    
def test_user_update():
    from shotglass2.users.models import User
    
    user = User(db)
    rec = user.get('doris')
    assert rec != None
    
    rec.email = 'AnewAddress@example.com'
    user.save(rec)
    rec = user.get('doris')
    assert rec.email == 'AnewAddress@example.com'
    
    db.rollback()
    
    #test the update() method of _Table
    rec = user.get('doris')
    d = {'id':233,'address':'1234 Some Street',}
    user.update(rec,d,True) #save to db
    rec = user.get('doris')
    assert rec.address == '1234 Some Street'
    assert rec.id != 233
        
    db.rollback()
    
def test_user_delete():
    from shotglass2.users.models import User
    
    user = User(db)
    record_deleted = user.delete(2)
    assert record_deleted == True
    record_deleted = user.delete('John')
    assert record_deleted == True
    record_deleted = user.delete('John') # can't delete it twice
    assert record_deleted == False
    record_deleted = user.delete('none') # test that we can delete an inactive record
    assert record_deleted == True
    db.rollback()
    
def test_user_profile_page(client):
        with client as c:
            from flask import session, g
            # attempt access without log in
            result = c.get('/user/edit',follow_redirects=True)  
            assert result.status_code == 200
            assert b'Login Required' in result.data
            
            #attempt to get admin access
            result = c.get('/user/edit/1/',follow_redirects=True)  
            assert result.status_code == 200
            assert b'Sorry. You do not have access to that page' in result.data

            #log in
            result = c.get('/login/')  
            assert result.status_code == 200
            assert b'User Name or Email Address' in result.data 

            result = c.post('login/', data={'userNameOrEmail': 'admin', 'password': 'password'},follow_redirects=True)
            assert result.status == '200 OK'
            assert b'Invalid User Name or Password' not in result.data
            assert session['user'] == 'admin'
    
            # load the user page
            result = c.get('/user/edit',follow_redirects=True)  
            assert result.status_code == 200
            assert b'Edit User' in result.data
                
def test_user_register(client):
        with client as c:
            from flask import session, g
            result = c.get('/user/register/',follow_redirects=True)  
            assert result.status_code == 200
            assert b'Account Registration' in result.data
            
            form_data = {
            'id':'0',
            'first_name':'Willie',
            'last_name': 'Nillie',
            'email': 'willie@testing.com',
            'new_username': 'testuser',
            'new_password': '',
            'confirm_password': '',
            'address': '',
            'address2': '',
            'city': '',
            'state': '',
            'zip': '',
            'phone': '',
            'active':1,
            }

            result = c.post('/user/register/', data=form_data,follow_redirects=True)
            assert result.status_code == 200
            assert b'Signup Successful' in result.data
            
            #test that duplicate name is rejected
            result = c.post('/user/register/', data=form_data,follow_redirects=True)
            assert result.status_code == 200
            assert b'That email address is already in use' in result.data
            assert b'That User Name is already in use' in result.data
            
            

############################ The final 'test' ########################
######################################################################

def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert True

