
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app
from shotglass2 import shotglass
from shotglass2.takeabeltof.get_client import client

#@pytest.fixture
#def client():
#    db_fd, app.app.config['DATABASE_PATH'] = tempfile.mkstemp()
#    app.app.config['TESTING'] = True
#    client = app.app.test_client()
#
#    with app.app.app_context():
#        with app.app.test_request_context():
#            #this context sets up a dummy request with a url of 'http://localhost/'
#            app.initalize_all_tables((app.get_db(app.app.config['DATABASE_PATH'])))
#        
#    yield client
#
#    os.close(db_fd)
#    os.unlink(app.app.config['DATABASE_PATH'])
    
    
filespec = os.path.join(os.path.dirname(os.path.realpath(__file__)),'instance/test.db')

db = None

def init_test_db():
    with app.app.app_context():
        db = app.get_db(filespec)
        app.initalize_all_tables(db)

        
def delete_test_db():
    if os.path.isabs(filespec):
        # delete the temp backup files
        test_dir = os.path.basename(filespec)
        file_list = os.listdir(test_dir)
        for f in file_list:
            os.remove(os.path.join(test_dir,f))
        os.rmdir(test_dir)
    else:
        os.remove(filespec)
        
        
def test_make_db_path():
    path = 'instance/notad.dat'
    assert shotglass.make_db_path(path) == True
    
    
def test_home(client):
    result = client.get('/')   
    assert result.status_code == 200 or result.status_code == 302
    #assert b'Hello World' in result.data 
    
def test_404(client):
    result = client.get('/nothingtofind')   
    assert result.status_code == 404
    assert b'Sorry' in result.data 
    
    
def test_refuse_instance(client):
    # any call with instnace in the url should be refused
    result = client.get('/docs/instance/site_settings.py')   
    assert result.status_code == 404
    result = client.get('/instance/site_settings.py')   
    assert result.status_code == 404
    result = client.get('/docs/instance/')   
    assert result.status_code == 404
    result = client.get('/docs/instance/database.sqlite')   
    assert result.status_code == 404
    result = client.get('/instance/database.sqlite')   
    assert result.status_code == 404
    

def test_do_backups():
    try:
        init_test_db()
    except:
        pass
    
    script_root = os.path.dirname(os.path.realpath(__file__))
    backup_dir_name = 'backup_test'
    backup_dir = os.path.join(script_root,backup_dir_name)
        
    with app.app.app_context():
        db_path = os.path.join(app.app.root_path,filespec)
        app.app.config['TESTING'] = True
        bac = shotglass.do_backups(db_path,force=True,backup_dir=backup_dir)
        
        assert bac.fatal_error == False
        assert bac.result_code == 0
        
        # delete the temp backup files
        file_list = os.listdir(backup_dir)
        for f in file_list:
            os.remove(os.path.join(backup_dir,f))
        os.rmdir(backup_dir)

    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        db.close()
        del db
        delete_test_db()
        assert True
    except:
        assert True
