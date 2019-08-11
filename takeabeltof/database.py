import sqlite3
from namedlist import namedlist #Like namedtuples but mutable
from shotglass2.takeabeltof.utils import cleanRecordID


class Database:
    """Handle the basic database functions, `filename` is the path to the sqlite3 database file."""
    def __init__(self,filename):
        self.filename = filename
        self.connection = None
    
    def connect(self):
        """Return a connection to the database"""
        self.connection = sqlite3.connect(self.filename)
        self.connection.row_factory = sqlite3.Row ## allows us to treat row as a dictionary
        self.connection.execute('PRAGMA foreign_keys = ON') #Turn on foreign key cascade support
        return self.connection
    
    def cursor(self):
        """Return a cursor to the current database"""
        if self.connection:
            return self.connection.cursor()
        else:
            raise sqlite3.DatabaseError('No connection opened to database')
    
    def close(self):
        if self.connection:
            self.connection.close()
            

class SqliteTable:
    """Handle some basic interactions with a table"""
    def __init__(self,db_connection):
        self.table_name = None
        self.db = db_connection
        self.order_by_col = 'id' #default orderby column(s)
        self.defaults = {}
        self._display_name = None #use to override the name display
        self.use_slots = True #Set to False to allow adding temporary fields to the list at runtime
        # self.indexes is a dictionary of <index name>:<index field defs>
        #   So, to create an index provide something like {"my_index":"contact_id, contact_name"}
        self.indexes = {}
        
    def commit(self):
        """A convenience to be able to call commit on the database from a table object"""
        self.db.commit()
        
    def create_table(self,definition=""):
        """The default table definition script. definition arg is a string of valid SQL"""
        
        # clean up the definition if needed
        definition = definition.rstrip()
        if definition != "":
            definition = ',' + definition.strip(',')
            
        sql = """CREATE TABLE IF NOT EXISTS '{}' (
            id INTEGER NOT NULL PRIMARY KEY{}
            )""".format(self.table_name,definition,)
        self.db.execute(sql)
        self.init_index()
        
    def init_index(self):
        for index_name,index_ref in self.indexes.items():
            self.db.execute("DROP INDEX IF EXISTS {}".format(index_name))
            self.db.execute("CREATE INDEX {} ON {}({})".format(index_name,self.table_name,index_ref))
        
    @property
    def display_name(self):
        if self._display_name:
            return self._display_name
            
        return '{}s'.format(self.table_name.replace('_',' ').title())

    def init_table(self):
        """Base init method. Just create the table"""
        self.create_table()

    def get_column_names(self):
        """Return a list of column names for the table"""
        out = []
        cols = self.db.execute('PRAGMA table_info({})'.format(self.table_name)).fetchall()
        for col in cols:
            out.append(col[1])
            
        return out
        
    @property
    def _data_tuple(self):
        """return a namedtuple for use with this table"""        
        return namedlist('DataRow',"{}".format(",".join(self.get_column_names())),default=None,use_slots=self.use_slots)
        
    def delete(self,id,**kwargs):
        """Delete a single row with this id.
        Return True or False"""
        
        #import pdb;pdb.set_trace()
        id = cleanRecordID(id)
        row = self.get(id,**kwargs)
        if row:
            self.db.execute('delete from {} where id = ?'.format(self.table_name),(id,))
            return True
               
        return False
        
    def query_one(self,sql):
        """Single row random query"""
        out = self.query(sql)
        if out != None:
            return out[0]
            
        return out
        
    def query(self,sql):
        """Perform a query that may return results from muliple tables
        The table instance you call this with is unimportant.
        You can call it on an instance of SqliteTable directly.
        Always make sure that you don't have conflicting field names in output.
        
        Returns None or a list
        """
        #import pdb;pdb.set_trace()
        out = None
        
        data = self.db.execute(sql).fetchall()
        if data != None and len(data) > 0:
            nl = namedlist('DataRow',"{}".format(",".join(data[0].keys())),default=None)
            out = [nl(*rec) for rec in data]
        return out
    
    def rows_to_namedlist(self,row_list):
        """return a list of namedlists based on the list of Row objects provided"""
        out = None
        if row_list and len(row_list)>0 and row_list[0] != None:
            out = [self._data_tuple(*rec) for rec in row_list]
        return out
        
    def new(self,set_defaults=True):
        """return an 'empty' namedlist for the table. Normally set the default values for the table"""
        rec = self._data_tuple()
        if set_defaults:
            self.set_defaults(rec)
        return rec
        
    def save(self,row_data,**kwargs):
        """Save the data in row_data to the db.
        row_data is a named list
        
        If row_data.id == None, insert, else update an existing record
        
        trim_strings=False in kwargs will write to db as received. else strip strings first
        commit=True in kwargs will commit the changes else changes are un-committed
        
        The data is re read from the db after save and row_data is updated in place so the calling methods has 
        an update version of the data.
        
        return the id value of the effected row
        
        """
        
        def get_params(row_data):
            """Get the values for the fields in this table that are included in row_data.
            
            Ignore elements of row_data where row_data contains values that are not part of this table
            such as when a join was used in the query.
            
            """
            params = ()
            fields = () # the fields from this table that are included in the row_data
            cols = self.get_column_names()
            #import pdb;pdb.set_trace()
            for x in range(1,len(cols)):
                if cols[x] in row_data._fields:
                    params += (row_data[row_data._fields.index(cols[x])],)
                    fields += (cols[x],)
            return params, fields
            
        strip_strings = kwargs.get('strip_strings',True) # Strip by default
        if strip_strings == True:
            for x in range(1,len(row_data)):
                if type(row_data[x]) is str:
                    row_data[x] = row_data[x].strip()
                    
        insert_new = False
        #generate the data param tuple
        
        if (row_data.id == None):
            insert_new = True
            self.set_defaults(row_data)
            params, fields = get_params(row_data)
            
            sql = 'insert into {} ({}) values ({})'.format(
                self.table_name,
                ",".join([fields[x] for x in range(len(fields))]),
                ','.join(["?" for x in range(len(fields))])
            )
        else:
            params, fields = get_params(row_data)
            #import pdb;pdb.set_trace()
            sql = 'update {} set {} where id = ?'.format(
                self.table_name,
                ",".join(["{} = ?".format(fields[x]) for x in range(len(fields))])
            )
            params +=(row_data.id,) # id to use in update where clause
                    
        # need to use a raw cursor so we can retrieve the last row inserted
        cursor = self.db.cursor()
        cursor.execute(sql,(params))
        
        if kwargs.get('commit',False):
            self.db.commit()
                
        if insert_new:
            row_id = cursor.lastrowid
        else:
            row_id = row_data.id
            
        # Don't use the self.get() method here because there may be constraints as in User
        temp_row = cursor.execute('select * from {} where id = {}'.format(self.table_name,row_id)).fetchone()
        
        if temp_row == None:
            raise TypeError
            #pass # Should really do something with this bit of infomation
        else:
            # upddate row_data with any values that may have changed
            for x in range(1,len(row_data)):
                if row_data._fields[x] in temp_row.keys():
                    row_data[x] = temp_row[row_data._fields[x]]
            
        row_data.id = row_id
                    
        return row_id
        
    def set_defaults(self,row_data):
        """When creating a new record, set the defaults for this table"""
        if row_data.id == None and len(self.defaults) > 0:
            row_dict = row_data._asdict()
            for key, value in self.defaults.items():
                if key in row_dict and row_dict[key] == None:
                    row_data._update({key:value})
        
    def _select_sql(self,**kwargs):
        """Return the sql text that will be used by select or select_one
        optional kwargs are:
            where: text to use in the where clause
            order_by: text to include in the order by clause
        """
        where = kwargs.get('where','1')
        order_by = kwargs.get('order_by',self.order_by_col)
        sql = 'SELECT * FROM {} WHERE {} ORDER BY {}'.format(self.table_name,where,order_by,)
        return sql
        
    def select(self,**kwargs):
        """
            perform a basic SELECT query returning a list namedlists for all columns
        """
        recs = self.db.execute(self._select_sql(**kwargs)).fetchall()
        if recs:
            return self.rows_to_namedlist(recs)
        return None
        
    def select_one(self,**kwargs):
        """a version of select method that returns a single named list object or None"""
        rows = self.rows_to_namedlist(
            [self.db.execute(
                self._select_sql(**kwargs)
                ).fetchone()]
            )
        return self._single_row(rows)
                
    def select_raw(self,sql,params=''):
        """Returns a list of named list objects based on the sql text with optional string substitutions"""
        return self.rows_to_namedlist(self.db.execute(sql,params).fetchall())
        
    def select_one_raw(self,sql,params=''):
        """Return a single namedlist for sql select statement"""
        return self._single_row(self.select_raw(sql,params))
            
    def get(self,id,**kwargs):
        """Return a single namedlist for the record specified by `id` or None"""
        return self._single_row(self.select(where='{}.id = {}'.format(self.table_name,cleanRecordID(id),)))
        
    def _single_row(self,rows):
        """Return the first element of list rows or else None"""        
        if rows:
            if len(rows) > 0:
                 return rows[0]
        return None
        
    def update(self,rec,form,save=False):
        """Update the rec with the matching elements in form
        rec is a record namedlist 
        form is an InmutableMultiDict or a dictionary object
        
        The id element is never updated. Before calling this method be sure that any elements
        in form that have names matching names in rec contain the values you want.
        
        Optionally can save the rec (but not committed) after update
        """
        #import pdb;pdb.set_trace()
        for key,value in rec._asdict().items():
            if key != 'id' and key in form:
                rec._update([(key,form[key])])
                
        if save:
            self.save(rec)
            
