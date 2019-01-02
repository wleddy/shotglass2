# takeabeltof.database.py

This module provides access to the Sqlite3 database.

---
> #### Database(*database_path*).connect() => sqlite3 connection

Connects to the database file. If the path is otherwise valid, a new empty database file is created when none exists.

---
> #### SqliteTable(*db_connection*) => self

This is the base object used to create table objects.

The following properties are set at creation:
> self.table_name = None  
> self.db = db_connection  
> self.order_by_col = 'id' #default orderby column(s)  
> self.defaults = {}  
> self._display_name = None #use to override the name display  
> self.use_slots = True #Set to False to allow adding temporary fields to the list at runtime  

---
> #### create_table(*self,definition=""*): => Nothing

Creates a table if one does not exist with the name set in self.table_name. definition is the sqlite code for the field 
definitions but without the "id" primary key field which is added here.

The function will not update an existing table. If the table exists, it does nothing.

---
> #### delete(*self,id,**kwargs*): => Bool

Delete the record with id = id. Returns True on success, else False.

---
> #### self.display_name => str

Returns the title formatted table name.

--- 
> #### get(*self,id,**kwargs*): => namedlist or None

Return a single namedlist where id = id or None

---
> #### get_column_names(self): => list[str]

Returns a list of the column names.

---
> #### init_table(self): => Nothing

Override this function to actually define your table.

---
> #### new(*self,set_defaults=True*): namedlist

Return an 'empty' namedlist for the table. Normally set the default values for the table

---
> #### rows_to_namedlist(*self,row_list*): => list[namedlist]

Return a list of namedlists based on the list of Sqlite Row objects provided. This function is useful to return a namedlist
when executing arbitrary sql code.

---
> #### > save(*self,row_data,**kwargs*): => int

Insert or Update the data in row_data to the db.

> row_data is a namedlist
> 
> If row_data.id == None, insert, else Update
> 
> trim_strings=False in kwargs will write to db as received. else strip blank space from values first
> 
> The data is re read-from the db after save and row_data is updated in place so the calling methods has 
> an update version of the data.
> 
> return the id value of the effected row

---
> #### select(self,***kwargs*): => list[namedlist] or None

Return a list of namedlists returned in query else None.

> optional kwargs are:
>> where: text to use in the where clause. If empty or missing, will return all records
>> order_by: text to include in the order by clause

---
> #### select_one(self,***kwargs*): => namelist or None

A single row version of select(). Returns a namedlist of the first record returned or None.

---
> #### select_raw(*self,sql,params=''*): => list[namedlist] or None

Returns a list of namedlist objects based on the sql text with optional string substitutions.

The substitutions are made using the built-in sqlite library '?' method. Considered a safer way of passing un-trusted
user input to the database.

---
> #### select_one_raw(*self,sql,params=''*): => namedlist or None

A single row version of select_raw()

---
> #### update(self,rec,form,save=False): => Nothing

Update the namedlist rec with the matching elements in form

> form is a dictionary like object
> 
> The id element is never updated. Before calling this method be sure that any elements
> in form that have names matching names in rec contain the values you want.
> 
> Optionally can save the rec (but not committed) after update

---
[Return to Docs](/docs/takeabeltof/README.md)

