import sys
sys.path.append('') ##get import to look in the working dir
import os

import app
import pytest
import sqlite3
import shotglass2.takeabeltof.database as dbm
from datetime import datetime, date


filespec = 'instance/test_database.db'
db = None

with app.app.app_context():
    app.app.config['TESTING'] = True

    db = app.get_db(filespec)
    app.init_db(db)

#table to test save...
from shotglass2.takeabeltof.database import SqliteTable

class PracticeTable(SqliteTable):
    """Create a simple table to work on"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'test_table'
        self.order_by_col = 'name'
        self.defaults = {'date_field':'now','datetime_field':'now','name':'Hello World!'}
        
    def create_table(self):
        """Define and create the role table"""
        
        sql = """
            'name' TEXT,
            'description' TEXT,
            'int_field' INTEGER,
            'number_field' NUMBER,
            'real_field' REAL,
            'float_field' FLOAT,
            'date_field' DATE,
            'datetime_field' DATETIME
             """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
        
    @property
    def _column_list(self):
        column_list = [
        {'name':'added_to_db','definition':'TEXT',},
        ]

        return column_list
        
        
    def create_with_add(self):
        sql = """
            'name' TEXT,
            'description' TEXT,
            'int_field' INTEGER,
            'number_field' NUMBER,
            'real_field' REAL,
            'float_field' FLOAT
             """
        super().create_table(sql,self._column_list)
        
        
def form():
    return {'name':"test name",'int_field':"0",'real_field':"this is not a number",'float_field':"100",'number_field':"30"}

def make_table():
    sql = f"drop table if exists {PracticeTable(db).table_name}"
    db.execute(sql)
    tester = PracticeTable(db)
    tester.create_table()
    return tester
    
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
    from app import app
    with app.app_context():
        # need the app_context because some of these raise errors
        tester = make_table()
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
        db.execute('DROP TABLE {}'.format(tester.table_name))
        with pytest.raises(sqlite3.OperationalError):
            assert tester.select()
            
            
    def test_add_extra_column():
        tester = make_table()
        rec = tester.new()
        form = {'name':"test name",'int_field':"0",'real_field':"this is not a number",'float_field':"100",'number_field':"30"}
        tester.update(rec,form,True)
        assert rec.name == "test name"
        assert rec.int_field == 0
        assert rec.real_field == "this is not a number"
        assert rec.float_field == 100.0
        assert rec.number_field == 30.0
        
        tester.create_with_add()
        rec = tester.select_one()
        assert rec != None
        assert rec.name == "test name"
        assert rec.int_field == 0
        assert rec.real_field == "this is not a number"
        assert rec.float_field == 100.0
        assert rec.number_field == 30.0
        
        assert rec.added_to_db == None
        
        # run again to be sure it's not added again
        tester.create_with_add() #added the column twice will raise OperationalError
         
def test_get():
    from app import app
    with app.app_context():
        # need the app_context because some of these raise errors
        form = {'name':"test name",'int_field':"0",}
        tester = make_table()
        rec = tester.new()
        tester.update(rec,form,True)
        
        rec2 = tester.get(rec.id)
        assert rec2
        assert rec2.name == 'test name'
        
        #Get with kwargs
        rec2 = tester.get(rec.id,commit=True)
        assert rec2
        assert rec2.name == 'test name'

class SecondHand:
    def __init__(self,connection):
        self.table = connection
        
    def delete(self,id):
        return self.table.delete(id,commit=True)
    
def test_secondhand_get():    
    tester = make_table()
    rec = tester.new()
    form = {'name':"test name",'int_field':"0",}
    tester.update(rec,form,True)
    
    rec = tester.get(1)
    assert rec
    sh = SecondHand(tester)
    success = sh.delete(1)
    assert success == True
    db.rollback()
    rec = tester.get(1)
    assert not rec
    
    
def test_record_save():
    tester = make_table()
    form = {'name':"save test",}
    where = 'name = "{}"'.format(form['name'])
    rec = tester.new()
    tester.update(rec,form)
    tester.save(rec)
    db.rollback() # this should undo the save
    rec = tester.select_one(where=where)
    assert rec == None
    
    rec = tester.new()
    tester.update(rec,form)
    tester.save(rec,commit=True)
    db.rollback() # this should have no effect
    rec = tester.select_one(where=where)
    assert rec != None
    
    
def test_record_instance_save():
    tester = make_table()
    form = {'name':"save test",}
    where = 'name = "{}"'.format(form['name'])
    rec = tester.new()
    rec.update(form)
    rec.save()
    db.rollback() # this should undo the save
    rec = tester.select_one(where=where)
    assert rec == None
    
    rec = tester.new()
    rec.update(form)
    rec.save(commit=True)
    db.rollback() # this should have no effect
    rec = tester.select_one(where=where)
    assert rec != None
    
    
def test_record_delete():
    tester = make_table()
    form = {'name':"delete test",}
    where = 'name = "delete test"'
    rec = tester.new()
    tester.update(rec,form)
    tester.save(rec,commit=True)
    db.rollback() # this should have no effect
    rec = tester.select_one(where=where)
    assert rec != None
    assert rec.name == form['name']
    result = tester.delete(rec.id)
    assert result == True
    rec = tester.select_one(where=where)
    assert rec == None

    # delete was not committed
    db.rollback()
    rec = tester.select_one(where=where)
    assert rec != None

    # delete with commit
    rec_id = rec.id
    assert rec_id > 0
    result = tester.delete(rec.id,commit=True)
    assert result == True
    rec = tester.select_one(where=where)
    assert rec == None
    db.rollback()
    # delete was not committed
    rec = tester.select_one(where=where)
    assert rec == None
    
    #try to delete the record again
    result = tester.delete(rec_id)
    assert result == False
    
def test_new_defaults():    
    tester = make_table()
    rec = tester.new()
    assert isinstance(rec.date_field,(date))
    assert isinstance(rec.datetime_field,(datetime))
    assert rec.name == 'Hello World!'
    
def test_query():    
    tester = make_table()
    rec = tester.new()
    assert isinstance(rec.date_field,(date))
    assert isinstance(rec.datetime_field,(datetime))
    assert rec.name == 'Hello World!'
    rec.save()
    assert rec.id is not None
    recs = tester.query(f"select * from {tester.table_name} where name = '{rec.name}'")
    assert recs is not None
    assert len(recs) == 1
    assert recs[0].name == 'Hello World!'
    
    
def test_query_one():    
    tester = make_table()
    rec = tester.new()
    assert rec.name == 'Hello World!'
    rec.save()
    assert rec.id is not None
    rec = tester.query_one(f"select * from {tester.table_name} where name = '{rec.name}'")
    assert rec is not None
    assert not isinstance(rec,list)
    assert rec.name == 'Hello World!'

############################ The final 'test' ########################
######################################################################

def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert "failed to delete test db" == ""
