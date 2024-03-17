from shotglass2.takeabeltof.database import SqliteTable
from shotglass2.takeabeltof.utils import cleanRecordID
from shotglass2.takeabeltof.date_utils import local_datetime_now, getDatetimeFromString
from shotglass2.users.views.password import getPasswordHash
import time
import random

class Role(SqliteTable):
    """Handle some basic interactions with the role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'role'
        self.order_by_col = 'lower(name)'
        self.defaults = {'rank':0,'lock':0}
        
    def create_table(self):
        """Define and create the role tablel"""
        
        sql = """
            'name' TEXT UNIQUE NOT NULL,
            'description' TEXT,
            'locked' INTEGER DEFAULT 0,
            'rank' INTEGER DEFAULT 0 """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """
    
        column_list = [
        # {'name':'expires','definition':'DATETIME',},
        ]
    
        return column_list

        
        
    def get(self,value):
        """Return a role with this value"""
        if isinstance(value,str):
            # if value is str, search by role.name
            return self.select_one(where="name = '{}'".format(value))
                
        return super().get(value)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
        
        #Try to get a value from the table and create records if none
        rec = self.db.execute('select * from {}'.format(self.table_name)).fetchone()
        if not rec:
            roles = [
                (None,'super','Super User',1,1000),
                (None,'admin','Admin User',1,500),
                (None,'user','Normal user',1,1),
            ]
            self.db.executemany("insert into {} values (?,?,?,?,?)".format(self.table_name),roles)
            self.db.commit()


class UserRole(SqliteTable):
    """Handle some basic interactions with the user_role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'user_role'
    
    def create_table(self):
        """Define and create the user_role tablel"""
        
        sql = """
            'user_id' INTEGER NOT NULL,
            'role_id' INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE RESTRICT """
        super().create_table(sql)
                
        
class User(SqliteTable):
    """Handle some basic interactions with the user table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'user'
        self.order_by_col = 'lower(last_name), lower(first_name)'
        self.defaults = {'active':1,}
        self.indexes = {"user_active":"active"}

    def _active_only_clause(self,include_inactive=False,**kwargs):
        """Return a clause for the select statement to include active only or empty string"""
        include_inactive = kwargs.get('include_inactive',include_inactive)
        if include_inactive:
            return ""
        
        return 'and user.active = 1'
        
    def add_role(self,user_id,role):
        """Add roles for the user. role param may be int or str of Role name"""
        user_id = cleanRecordID(user_id)
        role_id = -1
        if type(role) == str:
            rec = Role(self.db).get(role)
            if rec:
                role_id = rec.id
        else:
            role_id = cleanRecordID(role)
            
        if user_id > 0 and role_id > 0:
            self.db.execute('insert into user_role (user_id,role_id) values (?,?)',(user_id,role_id,))
        
    def delete(self,rec_id):
        """Delete a single user record as indicated
        'id' may be an integer or a string"""
        
        rec = self.get(rec_id,include_inactive=True)
        if rec:
            return super().delete(rec.id,include_inactive=True)
            
        return False
        
    def get(self,id,**kwargs):
        """Return a single Datarow instance or None for the user with this id.
        If 'id' is a string, try to find the user by username or email using self.get_by_username_or_email
        If include_inactive=True is in kwargs the search will include inactive users else they are excluded from 
        the result.
        """
        if type(id) is str:
            return self.get_by_username_or_email(id,**kwargs)
            
        include_inactive = kwargs.get('include_inactive',False)
        where = 'id = {} {}'.format(cleanRecordID(id),self._active_only_clause(include_inactive))

        return self.select_one(where=where)

    def get_by_username_or_email(self,nameoremail,**kwargs):
        """Return a single Datarow instance or None based on the username or email"""

        include_inactive = kwargs.get('include_inactive',False)

        sql = "select * from {} where (username = ? or lower(email) = lower(?)) {} order by id".format(self.table_name,self._active_only_clause(include_inactive))
        
        return self._single_row(self.select_raw(sql,(nameoremail.strip(),nameoremail.strip())))
    
    def get_roles(self,userID,**kwargs):
        """Return a list of the role DataRow objects for the user's roles"""
        
        order_by = kwargs.get('order_by','rank desc, name')
        sql = """select * from role where id in
                (select role_id from user_role where user_id = ?) order by {}
                """.format(order_by)
                
        return  Role(self.db).rows_to_data_row(self.db.execute(sql,(cleanRecordID(userID),)).fetchall())
        
    def max_role_rank(self,userID):
        """Return the higest role rank for the user specified"""
        max_rank = 0
        curr_user=self.get(userID)
        if curr_user:
            sql="""select coalesce(max(role.rank),0) as max_rank from user_role join role on user_role.role_id = role.id where user_role.user_id = {}""".format(curr_user.id)
            max_rank = self.query(sql)
            if max_rank:
                max_rank = max_rank[0].max_rank
            
        return max_rank
        
    def user_has_role(self,user_id,role_names):
        """Return True if user has the role role_name else False
         role_names may be a string or a list
        """
        if not role_names:
            return False
            
        if type(role_names) is not list:
            role_names = [role_names] # make list
            
        role_names = [x.lower() for x in role_names] #make lower
        
        roles = self.get_roles(user_id)
        if roles:
            role_name_list = [x.name.lower() for x in roles ]
            for this_role in role_names:
                if this_role in role_name_list:
                    return True
        
        return False
        
    def get_with_roles(self,role_list):
        """Return a list of users who have one or more of the roles in role_list
        Role list may be a list of role id's or it may be a DataRows of role records
        """
        if not isinstance(role_list,list):
            raise ValueError("role_list must be a list of records or ints")
            
        if isinstance(role_list[0],int):
            role_list = [str(i) for i in role_list]
        elif isinstance(role_list[0],str):
            role_list = [i for i in role_list]
        else:
            try:
                # must be a record list
                temp_list = [rec.id for rec in role_list]
                role_list = temp_list
            except Exception as e:
                raise ValueError("Not an expected type. Err> {}".format(str(e)))
                return None
                
        sql= """select * from user where id in (select user_id from user_role where role_id in ({})) order by {}""".format(','.join(role_list),self.order_by_col)
        recs = self.query(sql)
        return recs
                
    def select(self,**kwargs):
        """ Custom select for User table
        kwargs:
            where -> str: the where clause to use. defaults to "1"
            include_inactive -> bool: should inactive users be included. defaults to False
            user_status_select -> str: Overrides include_inactive. may be any of -1, 0, or 1.
                -1 means include all users
                1 means active users only
                0 means inactive users only
            role_id_list_select -> list: a list of role id's used to limit the selection
        """
        # import pdb;pdb.set_trace()
        where = f"{kwargs.get('where','1')} "

        # set to active only by default
        active_user_clause = self._active_only_clause(kwargs.get('include_inactive',False))

        # include_inactive and user_status_select may both be in kwargs
        # If so, user_status_select takes precedent
        if "user_status_select" in kwargs:
            active_user_clause = '' # include all
        if kwargs.get("user_status_select",'-1') != "-1":
            # -1 means show all users, 0 is inactive only, 1 is active only
            active_user_clause = f' and active = {kwargs["user_status_select"]} '

        # Filter by role?
        roles_where_clause = ''
        if "role_id_list_select" in kwargs and kwargs['role_id_list_select'] and 0 not in kwargs['role_id_list_select']:
            str_ids = [str(x) for x in kwargs['role_id_list_select']]
            roles_where_clause = f" and role.id in ({','.join(str_ids)})"


        order_by = kwargs.get('order_by',self.order_by_col)

        limit = kwargs.get('limit',9999999)
        offset = kwargs.get('offset',0)
        
        sql = f"""select user.*,
                    user.first_name || ' ' || user.last_name as full_name,
                    max(role.rank) as max_rank,
                    "" as roles
                from user
                join user_role on user_role.user_id = user.id
                join role on role.id = user_role.role_id
                where {where} --lower(role.name) in ('admin') 
                {active_user_clause}
                {roles_where_clause}
                group by user.id
                order by {order_by}
                limit {limit} offset {offset}
            """
        
        recs = self.query(sql)
        if recs:
            for rec in recs:
                rec.max_rank = self.max_role_rank(rec.id)
                
                # Create a semi-colon separated text list of user roles
                role_sql = """
                select
                role.*
                    from user_role 
                    join role on role.id = user_role.role_id
                    where user_role.user_id = {}
                    order by role.name
                """.format(rec.id)
                #import pdb;pdb.set_trace()
                roles = self.query(role_sql)
                
                if roles:
                    role_list = [x.name for x in roles]
                    role_list = ";".join(role_list)
                    rec.roles = role_list
                    
            return recs
            
        return None
        
    def update(self,rec,form,save=False):
        # active must be an integer
        if 'active' in form and type(form['active']) is str:
            super().update(rec,form,False)
            rec.active = int(rec.active)
            form = rec.asdict()
        # update normally and save is requested
        super().update(rec,form,save)
            
        
    def update_last_access(self,user_id,no_commit=False):
        """Update the 'last_access' field with the current datetime. Default is for record to be committed"""
        if type(user_id) is int:
            self.db.execute('update user set last_access = ? where id = ?',(local_datetime_now(),user_id,))
            if not no_commit:
                # import pdb;pdb.set_trace()
                try:
                    self.db.commit()
                except Exception as e:
                    from app import app
                    app.logger.exception(f'[{local_datetime_now()}] -- Error while committing to user table {str(e)}')
                    self.db.rollback()
                    
    def clear_roles(self,user_id):
        """Delete all user_role records from this user"""
        self.db.execute('delete from user_role where user_id = ?',(cleanRecordID(user_id),))
        
    def create_table(self):
        """Define and create the user tablel"""
        
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT UNIQUE COLLATE NOCASE,
            'phone' TEXT,
            'address' TEXT,
            'address2' TEXT,
            'city' TEXT,
            'state' TEXT,
            'zip' TEXT,
            'username' TEXT UNIQUE,
            'password' TEXT,
            'active' INTEGER DEFAULT 1,
            'last_access' DATETIME,
            'access_token' TEXT,
            'access_token_expires' INT,
            'may_send_text' INT,
            'may_send_email' INT
            """
        super().create_table(sql)
        
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
        column_list = [
            {'name':'created','definition':'DATETIME',},
            ]

        return column_list
        
    def init_table(self):
        """add some initial data"""

        self.create_table()
        
        #Try to get a value from the table and create a record if none
        rec = self.db.execute('select * from {}'.format(self.table_name)).fetchone()
        if not rec:
            sql = """insert into {}
                (first_name,last_name,username,password)
                values
                ('Admin','User','admin','{}')
            """.format(self.table_name,getPasswordHash('password'))
            self.db.execute(sql)
            #self.db.commit()
            
            # Give the user super powers
            rec = self.get(1)
            userID = rec.id
            rec = Role(self.db).select_one(where='name = "super"')
            roleID = rec.id
            self.db.execute('insert into user_role (user_id,role_id) values (?,?)',(userID,roleID))
            self.db.commit()

    def is_admin(self,user):
        """Return True if user (name or id) is an admin"""
        from shotglass2.shotglass import get_site_config
        
        rec = self.get(user)
        if not rec:
            return False
        admin_roles = get_site_config().get('ADMIN_ROLES',['super','admin',])
        user_roles = self.get_roles(rec.id)
        if user_roles:
            for role in user_roles:
                if role.name in admin_roles:
                    return True
        return False
        
        
    def save(self,rec,**kwargs):
        #populate the created field if null
        if rec.created == None:
            if rec.last_access is not None:
                rec.created = rec.last_access
            else:
                rec.created = local_datetime_now()
        
        return super().save(rec,**kwargs)
        
        
class Pref(SqliteTable):
    """
        A table to store some random data in
        Prefs can be global or attached to a single user
        Prefs can also be set to expire
    """
    
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'pref'
        self.order_by_col = 'name'
        self.defaults = {}
        
    def create_table(self):
        """Define and create the table"""

        sql = """
            name TEXT,
            value TEXT,
            expires DATETIME,
            user_name TEXT
            """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """

        column_list = [
            {'name':'description','definition':'TEXT',},
        ]

        return column_list
        

    def get(self,name,user_name=None,**kwargs):
        """can get by pref name and user_name"""
        user_clause = 'and user_name is null'
        if user_name:
            user_clause = 'and user_name = "{}"'.format(user_name)
        
        if type(name) is str:
            where = ' lower(name) = lower("{}") {}'.format(name,user_clause)
        else:
            where = ' id = {}'.format(cleanRecordID(name))
            
        result = self.select_one(where=where)
        
        if not result and ('default' in kwargs or 'description' in kwargs) and type(name) is str:
            # create a record with the default values
            rec = self.new()
            rec.name = name
            rec.value = kwargs['default']
            rec.user_name = user_name
            rec.expires = kwargs.get('expires')
            rec.description = kwargs.get("description")
            self.save(rec)
            self.db.commit()
            result = rec
            
        return result
    

class VisitData(SqliteTable):
    """
        A table to store a visitor's session data between requests.

        My Session data has got too big for the officially allowed browser space.
        The session data will now be stored here and reloaded into session with
        each request.

    """
    
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'visit_data'
        self.order_by_col = 'id'
        self.defaults = {'value':'','user_name':'Unknown'}
        
    def create_table(self):
        """Define and create the table"""

        sql = """
            session_id TEXT,
            user_name TEXT,
            value TEXT,
            expires DATETIME,
            """
        super().create_table(sql)
        
        
    @property
    def _column_list(self):
        """A list of dicts used to add fields to an existing table.
        """

        column_list = []

        return column_list
    
    def _is_expired(self,rec: object) -> True | False :
        """Return True if record has expired else False"""

        if rec and rec.expires:
            ex =  getDatetimeFromString(rec.expires)
            if ex and ex < local_datetime_now():
                return True
            
        return False


    def delete(self,identifier: str | int) ->bool:
        """Accept Session_id or record id for deletion"""
        rec = self.get(identifier)
        if rec:
            return super().delete(rec.id)

        return False


    def get(self,value: str | int,**kwargs) -> object | None:
        """can get by data by id or session_id"""
        if isinstance(value,int) or value.isnumeric():
            where = ' id = {}'.format(cleanRecordID(value))
        elif isinstance(value,str):
            where = f' session_id = "{value}"'
        else:
            return None
            
        rec =  self.select_one(where=where)

        #Check expires date
        if self._is_expired(rec):
            rec = None

        return rec
    

    def new(self) -> object:
        """Create a new VisitData record and assign a session_id"""

        from shotglass2.shotglass import get_site_config

        rec = super().new()

        found_match = True
        while found_match:
            rec.session_id = get_site_config()['HOST_NAME'] + "_"
            rec.session_id += str(getPasswordHash(str(time.time() + random.randint(100,1000))))
            found_match = self.get(rec.session_id) is not None

        return rec
    
    def prune(self) -> None:
        """
        Remove and out of date or otherwise undesirable visit records.
        """
        sql = """
            select id from visit_data where
                expires is not null and 
                date(expires,'localtime') < date("{now}",'localtime')
        
            """.format(now=local_datetime_now())
        
        recs = self.query(sql)
        
        if recs:
            for rec in recs:
                    self.delete(rec.id)


    def save(self,rec:object) -> object:
        """Update the expires field and save the record"""
        from shotglass2.shotglass import get_site_config
        rec.expires = local_datetime_now() + get_site_config()['PERMANENT_SESSION_LIFETIME']
        super().save(rec)
        self.commit()

        return rec

        
def init_db(db):
    """Create Tables."""
    l = globals().copy()
    for n,o in l.items():
        if type(o) == type and \
            issubclass(o,SqliteTable) and \
            o != SqliteTable:
    
            o(db).init_table()
    