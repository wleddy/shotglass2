import sys
sys.path.append('') ##get import to look in the working dir
import os

import app
import sqlite3
import shotglass2.takeabeltof.database as dbm

filespec = 'instance/test_database.db'
db = None
app.app.testing = True

with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)

#table to test save...
from shotglass2.takeabeltof.database import SqliteTable

class SaveTest(SqliteTable):
    """Handle some basic interactions with the role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'save_test'
        self.order_by_col = ''
        self.defaults = {}
        
    def create_table(self):
        """Define and create the role tablel"""
        
        sql = """
            'name' TEXT,
            'description' TEXT,
            'int_field' INTEGER,
            'number_field' NUMBER,
            'real_field' REAL,
            'float_field' FLOAT
             """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
        


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
    
def test_numeric_field_save():
    import app
    with app.app.app_context():
        tester = SaveTest(db)
        tester.create_table()
        rec = tester.new()
        form = {'name':"test name",'int_field':"0",'real_field':"this is not a number",'float_field':"100",'number_field':"30"}
        tester.update(rec,form,True)
        assert rec.name == "test name"
        assert rec.int_field == 0
        assert rec.real_field == "this is not a number"
        assert rec.float_field == 100.0
        assert rec.number_field == 30.0
        form = {'name':"test name",'int_field':100.345,'real_field':30.2,'float_field':100.34,'number_field':700.2}
        tester.update(rec,form,True)
        assert rec.name == "test name"
        assert rec.int_field == 100
        assert rec.real_field == 30.2
        assert rec.float_field == 100.34
        assert rec.number_field == 700.2
        form = {'name':"test name",'int_field':None,'real_field':None,'float_field':None,'number_field':None}
        tester.update(rec,form,True)
        assert rec.name == "test name"
        assert rec.int_field == None
        assert rec.real_field == None
        assert rec.float_field == None
        assert rec.number_field == None
        
        db.rollback()
        
    
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
