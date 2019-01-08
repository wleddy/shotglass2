import sys
sys.path.append('') ##get import to look in the working dir
import os

import app
import sqlite3
import shotglass2.takeabeltof.database as dbm

filespec = 'instance/test_database.db'
db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)

def delete_test_db():
        os.remove(filespec)

def test_database():
    assert type(db) is sqlite3.Connection
    assert db.row_factory == sqlite3.Row
    rec = db.execute('PRAGMA foreign_keys').fetchone()
    assert rec[0] == 1 # foreign key support is on
    
def test_database_cursor():
    cursor = db.cursor()
    assert type(cursor) == sqlite3.Cursor
    
    
### Should test the SqliteTable class here, but too tired now...
    
    

############################ The final 'test' ########################
######################################################################

def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert "failed to delete test db" == ""
