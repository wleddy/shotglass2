import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.
import os
import pytest
#from app import app
from shotglass2.takeabeltof.sqlite_backup import SqliteBackup

# create an empty sqlite file for testing
from shotglass2.takeabeltof.database import Database
script_root = os.path.dirname(os.path.realpath(__file__))
backup_dir_name = 'backup_test'
backup_dir = os.path.join(script_root,backup_dir_name)
backup_file_name = 'test_db.sqlite'
file_name = os.path.join(script_root,backup_file_name)
conn = Database(file_name).connect()


def test_backup():
    bac = SqliteBackup(file_name,frequency=0,backup_dir=backup_dir,force=True)
    bac.backup()
    
    assert bac.result_code ==  0
    assert "Success" in bac.result
    assert bac.fatal_error == False
    assert os.path.isdir(backup_dir)
    file_list = os.listdir(backup_dir)
    assert len(file_list) > 0
    assert 'data_hash.txt' in file_list
    assert any(s.startswith(backup_file_name) for s in file_list) == True
        
def test_no_data_change():
    bac = SqliteBackup(file_name,frequency=0,backup_dir=backup_dir)
    bac.backup()
    
    assert bac.result_code == 2
    assert bac.fatal_error == False
            
def test_too_soon():
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_me (a_field Number)")
    cur.execute('INSERT INTO test_me values (5)')
    conn.commit()
    bac = SqliteBackup(file_name,backup_dir=backup_dir)
    bac.backup()
    
    assert bac.result_code == 1
    assert bac.fatal_error == False

def test_missing_db():
    bac = SqliteBackup(file_name+"something",frequency=0,backup_dir=backup_dir,force=True)
    bac.backup()
    
    assert bac.fatal_error == True
    assert bac.result_code == 10
        
            
def test_cleanup():
    conn.close()
    os.remove(file_name)
    file_list = os.listdir(backup_dir)
    for f in file_list:
        os.remove(os.path.join(backup_dir,f))
    os.rmdir(backup_dir)
    

