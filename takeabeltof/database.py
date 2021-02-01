import sqlite3
import warnings
from flask import flash
from shotglass2.takeabeltof.utils import cleanRecordID ,printException
from shotglass2.takeabeltof.date_utils import getDatetimeFromString, local_datetime_now
from datetime import datetime
# from shotglass2.takeabeltof.mailer import email_admin


class Database:
    """Handle the basic database functions
    
    Args:
        filename: string, Path to the sqlite3 database file.
        
    """
    def __init__(self,filename):
        self.filename = filename
        self.connection = None
    
    def __exit__(self):
        # close the connection if opened within an "with" block
        self.connection.close()
            
            
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
        self.__exit__()
            

class SqliteTable:
    """Represents a SQLite3 table
    
    Args:
        db_connection: Database.connect() object, the connection to the database
        
    """
    
    def __init__(self,db_connection):
        self.table_name = None
        self.db = db_connection
        self.order_by_col = 'id' #default orderby column(s)
        self.defaults = {}
        self._display_name = None #use to override the name display
        self.use_slots = True #Set to False to allow adding temporary fields to the list at runtime
        # self.indexes is a dictionary of <index name>:<field name(s) to index>
        #   So, to create an index provide something like {"my_index":"contact_id",}
        #   If you redefine an existing index, be sure to drop it manually before first run.
        self.indexes = {}
        
        # certain column type should not be set to text values
        self.float_types = ['FLOAT','REAL','NUMBER']
        self.integer_types = ['INTEGER','INT',]
        self.numeric_types = []
        self.numeric_types.extend(self.float_types)
        self.numeric_types.extend(self.integer_types)
        
    def alert_admin(self,message):
        """Send an email to the admin address if an error is encountered or
        if you just fell like talking...
    
        """
        from shotglass2.takeabeltof.mailer import email_admin
        from shotglass2.shotglass import get_site_config
    
        email_admin("Error in database access for {}".format(get_site_config()['HOST_NAME']),message)

    def commit(self):
        """A convenience to be able to call commit on the database from a table object"""
        self.db.commit()
        
    def create_table(self,definition="",column_list=[]):
        """The default table definition script. definition arg is a string of valid SQL"""
        
        # clean up the definition if needed
        definition = definition.rstrip()
        if definition != "":
            definition = ',' + definition.strip(',')
            
        sql = """CREATE TABLE IF NOT EXISTS '{}' (
            id INTEGER NOT NULL PRIMARY KEY{}
            )""".format(self.table_name,definition,)
        self.db.execute(sql)
        # additional fields?
        column_list = column_list if column_list else self._column_list
        self._add_columns(column_list)
        self.init_index()
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        
        The primary purpose is to allow for a simple way to add columns to a
        table that already exists. You need to manually create a list of dicts
        as below in the table class, copy this method as a template and override 
        the create table method with something like:
            `self.create_table(sql,self._column_list)`
            
        Note: Because of the limitations of Sqlite3, columns created via ALTER TABLE
        may not contain UNIQUE constraints. There also may not be a NOT NULL constraint
        unless the definition includes a DEFAULT value
        
        The added column definitions look like this:
            `column_list = [
            {'name':'name','definition':'TEXT',},
            {'name':'value','definition':'TEXT',},
            {'name':'expires','definition':'DATETIME',},
            {'name':'user_name','definition':'TEXT',},
            {'name':'a_number_field','definition':'NUMBER',},
            ]
            
            return column_list`
        """
    
        return []
        
        
    def _add_columns(self,column_list=[]):
        """A simple way to add new columns to the table.
        
        Note: Because of the limitations of Sqlite3, columns created via ALTER TABLE
        may not contain UNIQUE constraints. There also may not be a NOT NULL constraint
        unless the definition includes a DEFAULT value
        
        """
        for column in column_list:
            col_name = column.get('name','')
            col_def = column.get('definition','')
            if col_name and col_def and col_name not in self.get_column_names():
                self.db.execute('ALTER TABLE {} ADD COLUMN {} {}'.format(
                    self.table_name,
                    col_name,
                    col_def,
                    )
                )
        
    def init_index(self):
        for index_name,index_ref in self.indexes.items():
            self.db.execute("CREATE INDEX IF NOT EXISTS {} ON {}({})".format(index_name,self.table_name,index_ref))
        
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
            out.append(col['name'])
            
        return out
 
    def get_column_type(self,column_name):
        """Return the Sqlite column type (as text) for the specified column name
        
        Always wrap calls to this method in a try block to catch the KeyError
        and handle the case where the (adhoc) column name is not in the table such
        as the case when a column is included as the result of a table join.
        
        """
        #import pdb;pdb.set_trace()
        out = None
        cols = self.db.execute('PRAGMA table_info({})'.format(self.table_name)).fetchall()
        
        for col in cols:
            if col[1] == column_name:
                out = col['type'].upper()
                break
            
        if out == None:
            raise KeyError("That column name is not in this table")
            
        return out
       

    def _get_data_row(self,column_names=[],row_data=None):
        """return an instance DataRow for this table
        
        DataRow will have attributes for the items in column_names
        
        Args:
            column_names: list, a list column names or all columns for this table
            row_data: dict | sqlite3.Row() | None, Data to be applied to matching column names, if any
        """
        # import pdb;pdb.set_trace()
        column_names = column_names or self.get_column_names()
                
        return DataRow(self,column_names,row_data)
        
        
    def delete(self,id,**kwargs):
        """Delete a single row with this id.
        Return True or False"""
        
        #import pdb;pdb.set_trace()
        id = cleanRecordID(id)
        row = self.get(id,**kwargs)
        if row:
            self.db.execute('delete from {} where id = ?'.format(self.table_name),(id,))
            if kwargs.get('commit',False):
                self.db.commit()
                
            return True
               
        return False
        
    def query_one(self,sql):
        """Single row random query"""
        out = self.query(sql)
        if out != None:
            return out[0]
            
        return out
        
    def query(self,sql):
        """Perform a query that may return results from multiple tables
        The table instance you call this with is unimportant.
        You can call it on an instance of SqliteTable directly.
        Always make sure that you don't have conflicting field names in output.
        
        Returns None or a list
        """
        # import pdb;pdb.set_trace()
        out = None
        
        data = self.db.execute(sql).fetchall()
        if data != None and len(data) > 0:
            out = self.rows_to_data_row(data)
        return out
    
    def rows_to_namedlist(self,row_list):
        warnings.warn(DeprecationWarning("SqliteTable.rows_to_namedlist is deprecated, Use rows_to_data_row instead."))
        
        return self.rows_to_data_row(row_list)
        
    def rows_to_data_row(self,row_list):
        """return a list of DataRow objects based on the list of Row objects provided"""
        # import pdb;pdb.set_trace()
        out = None
        if row_list and len(row_list)>0 and row_list[0] != None:
            out = [self._get_data_row(rec.keys(),rec) for rec in row_list]
        return out
        
    def new(self,set_defaults=True):
        """return an 'empty' DataRow object for the table. Normally set the default values for the table"""
        rec = self._get_data_row()
        if set_defaults:
            self.set_defaults(rec)
        return rec
        
    def save(self,rec,**kwargs):
        """Save the data in rec to the db.
        rec is a named list
        
        If rec.id == None, insert, else update an existing record
        
        trim_strings=False in kwargs will write to db as received. else strip strings first
        commit=True in kwargs will commit the changes else changes are un-committed
        
        The data is re read from the db after save and rec is updated in place so the calling methods has 
        an update version of the data.
        
        return the id value of the effected row
        
        """
        
        def get_params(rec):
            """Get the values for the fields in this table that are included in rec.
            
            Ignore elements of rec where rec contains values that are not part of this table
            such as when a join was used in the query.
            
            """
            params = ()
            fields = () # the fields from this table that are included in the rec
            cols = self.get_column_names()
            # import pdb;pdb.set_trace()
            for x in range(1,len(cols)):
                if cols[x] in rec._fields:
                    params += (rec.get(cols[x]),)
                    fields += (cols[x],)
            return params, fields
            
        strip_strings = kwargs.get('strip_strings',True) # Strip by default
        if strip_strings == True:
            for key, value in rec.items():
                if isinstance(value,str):
                    setattr(rec, key, value.strip())
                    
        insert_new = False
        #generate the data param tuple
        
        # import pdb;pdb.set_trace()
        
        if (rec.id == None):
            insert_new = True
            self.set_defaults(rec)
            params, fields = get_params(rec)
            
            sql = 'insert into {} ({}) values ({})'.format(
                self.table_name,
                ",".join([fields[x] for x in range(len(fields))]),
                ','.join(["?" for x in range(len(fields))])
            )
        else:
            params, fields = get_params(rec)
            #import pdb;pdb.set_trace()
            sql = 'update {} set {} where id = ?'.format(
                self.table_name,
                ",".join(["{} = ?".format(fields[x]) for x in range(len(fields))])
            )
            params +=(rec.id,) # id to use in update where clause
                    
        # need to use a raw cursor so we can retrieve the last row inserted
        cursor = self.db.cursor()
        cursor.execute(sql,(params))
        
        if kwargs.get('commit',False):
            self.db.commit()
                
        if insert_new:
            row_id = cursor.lastrowid
        else:
            row_id = rec.id
            
        # Don't use the self.get() method here because there may be constraints as in User
        temp_row = cursor.execute('select * from {} where id = {}'.format(self.table_name,row_id)).fetchone()
        
        if temp_row == None:
            raise sqlite3.OperationalError(f"Failed to save record in table {self.table_name}.")
            #pass # Should really do something with this bit of infomation
        else:
            # upddate rec with any values that may have changed
            for x in range(1,len(rec)):
                if rec._fields[x] in temp_row.keys():
                    temp_value = temp_row[rec._fields[x]]
                    col_type = self.get_column_type(rec._fields[x]).upper()
                    # try to ensure that the data is the correct type
                    if type(temp_value) is str and col_type in self.numeric_types:
                        #Try to convert this string to a number
                        temp_value = self._text_to_numeric(rec._fields[x],temp_value,col_type)
                    elif type(temp_value) == int and col_type in self.float_types:
                        temp_value = temp_value + 0.0
                    elif type(temp_value) == float and col_type in self.integer_types:
                        temp_value = int(temp_value)
                    
                    setattr(rec, rec._fields[x], temp_value)
                    
        rec.id = row_id
                    
        return row_id
        
    def set_defaults(self,rec):
        """When creating a new record, set the defaults for this table.
        
        If the column is type datetime or date and the default value is 'now', insert
        the current date or datetime
        
        """
        if rec.id == None and len(self.defaults) > 0:
            # row_dict = rec._asdict()
            for key, value in self.defaults.items():
                if key in rec and rec.get(key) == None:
                    if value == 'now':
                        col_type = self.get_column_type(key)
                        if col_type.upper() == 'DATE':
                            value = local_datetime_now().date()
                        if col_type.upper() == 'DATETIME':
                            value = local_datetime_now()
                    setattr(rec, key, value)

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
            perform a basic SELECT query returning a list DataRow objects for all columns
        """
        recs = self.db.execute(self._select_sql(**kwargs)).fetchall()
        if recs:
            return self.rows_to_data_row(recs)
        return None
        
    def select_one(self,**kwargs):
        """a version of select method that returns a single named list object or None"""
        rows = self.rows_to_data_row(
            [self.db.execute(
                self._select_sql(**kwargs)
                ).fetchone()]
            )
        return self._single_row(rows)
                
    def select_raw(self,sql,params=''):
        """Returns a list of named list objects based on the sql text with optional string substitutions"""
        return self.rows_to_data_row(self.db.execute(sql,params).fetchall())
        
    def select_one_raw(self,sql,params=''):
        """Return a single DataRow object for sql select statement"""
        return self._single_row(self.select_raw(sql,params))
            
    def get(self,id,**kwargs):
        """Return a single DataRow object for the record specified by `id` or None"""
        return self._single_row(self.select(where='{}.id = {}'.format(self.table_name,cleanRecordID(id),)))
        
    def _single_row(self,rows):
        """Return the first element of list rows or else None"""        
        if rows:
            if len(rows) > 0:
                 return rows[0]
        return None
        
    def _text_to_numeric(self,field_name,value,column_type):
        """Attempt to coerce values for numeric fields to numbers if needed.
        
        Params:
        
            field_name: the name of the field being updated
            
            value: the value to convert
            
            column_type: the text name of the field type e.g. INTEGER, REAL, etc.
            
        Return the number or the original value if not successful
        
        Alerts admin on failure
        
        """
        
        from shotglass2.shotglass import get_site_config

        value = value.strip()
        column_type = column_type.upper()
        
        if type(value) != str:
            #safety valve
            return value
            
        if value == '':
           value = None
        elif value.isdigit():
           # convert to int
           value = int(value)
        else:
           # may be a float
           try:
               value = float(value)
               if column_type in self.integer_types:
                   value = int(value)
           except Exception as e:
                mes ="""A problem occurred while attempting to save the record for table {}. 
                It looks like a non-numeric value ('{}') was entered in the field '{}'.
                
                The information in the record may not be what you expect...

                """.format(self.table_name.title(),value,field_name)
                if not get_site_config()['TESTING']:
                    flash(mes)
                self.alert_admin(printException(mes,err=e))
               
        return value
        
        
    def update(self,rec,form,save=False):
        """Update the rec, with the matching elements in form
        
        Args:
            rec: dictionary like object, represents an existing or new reocrd or
            a dict of values to be applied to the current current record.
        
        form is a dictionary like object with the new data. Usually request.form
        
        The id element is never updated. Before calling this method be sure that any elements
        in form that have names matching names in rec contain the values you want.
        
        Optionally can save the rec (but not committed) after update
        """

        # import pdb;pdb.set_trace()
        if rec and form:
            data_dict = rec._asdict()
                
            # for key,value in data_dict.items():
            for key,value in rec.items():
                if key != 'id' and key in form:
                    val = form[key]
                    try: # if key is an adhoc column name that was defined in a query, no update required
                        # Dates need special formatting
                        col_type = self.get_column_type(key).upper()
                        if col_type == 'DATETIME' or col_type == 'DATE':
                            if not isinstance(val,datetime):
                                val = getDatetimeFromString(val)
                                
                        setattr(rec, key, val)
                        
                    except KeyError:
                        pass
                
            if save:
                self.save(rec)
            
            
class DataRow:
    """Represents a single row of data in the source table

    Args:
        source_table: SqliteTable instance, The table being accessed
        col_list: list, Names of columns in table
        col_data_dict: dict or sqlite3.Row, a dict of column names and their values. 
            Column value defaults to None if not present in dict.

    Returns: Nothing

    Raises:
        ValueError if attempting to set source_table after __init__
        TypeError if source_table is not instance of SqliteTable
        TypeError if col_data_dict is not a dict or instance of sqlite3.Row
        TypeError if col_list is not a list

    """

    def __init__(self,source_table,col_list,col_data_dict={}):
        if not isinstance(source_table,SqliteTable):
            raise TypeError("Source Table must be instance of SqliteTable")

        super().__setattr__('source_table',source_table)

        col_data_dict = col_data_dict or {}
            
        if isinstance(col_data_dict,sqlite3.Row):
            # Convert the Row to a dict
            temp_dict = dict()
            for key in col_data_dict.keys():
                temp_dict.update({key:col_data_dict[key],})
                
            col_data_dict = temp_dict
            
        if not isinstance(col_data_dict,dict):
            raise TypeError("DataRow column data must be a dict.")

        if not isinstance(col_list,list):
            raise TypeError("col_list must be a list")

        self._keys = []
        for key in col_list:
            self._keys.append(key)
            setattr(self,key,col_data_dict.get(str(key)))


    def __contains__(self,val):
        return val in self._keys

    def __iter__(self):
        for item in self._keys:
            yield item

    def __len__(self):
        return len(self._keys)
        
    def __repr__(self):
        return f"DataRow: {self.source_table.table_name}:{self.asdict()}"

    def __setattr__(self,prop,value):
        # can't modify the source_table list outside of __init__
        if prop is 'source_table':
            raise ValueError('DataRow source_table property may not be set.')

        super().__setattr__(prop,value)


    def _asdict(self):
        "for compatability with old namedlist methods"
        return self.asdict()

    @property
    def _fields(self):
        """Return a list of field names

        This is form compatability with the old namedlist methods
        """
        return self._keys

    def asdict(self):
        out = dict()
        for key, value in self.items():
            out.update({key:value,})
        return out

    def commit(self):
        self.source_table.commit()

    def keys(self):
        for key in self._keys:
            yield key

    def get(self,key,default=None):
            return getattr(self,key,default)

    def items(self):
        for key in self._keys:
            yield (key,self.__getattribute__(key),)

    def save(self,commit=False):
        # import pdb;pdb.set_trace()
        return self.source_table.save(self,commit=commit)

    def update(self,data,save=False):
        # import pdb;pdb.set_trace()
        return self.source_table.update(self,data,save)

    