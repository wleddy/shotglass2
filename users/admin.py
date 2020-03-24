"""
admin.py
-----------
This module provides user access control.

It's primarily based on which database tables a user can see / update

"""


from flask import g, request, redirect, url_for, flash
from functools import wraps

class Admin():
    """A class to hold the list of access privilege requirements for database
    tables.
    
    The items in the Admin list may be used to create menu items for the web site and
    also provides functions to test the current users access privileges.
    
    Instanciate as:
        admin = Admin(*database connection*)
        
    When assessing permissions test that the specified user (by id or username) has:
         a role with at least minimum_rank_required
         OR
         a role (by name) in the list roles
    """
    
    def __init__(self,db):
        self.db = db #A database connection. need it to instanciate tables
        self.permissions = []
        
    def register(self,table,url,**kwargs):
        """Add a table item to the .permissions list
        
        Arguments:
            table : Database table object
            url : str The url to be associated with the menu item created for this table
                
        kwargs:
            display_name: <str> None
                The name that will be used in the menu item
            header_row: <bool> False,
                Is this the header row for a drop down menu. 
            top_level: <bool> False,
                Is this a menu stand-alone menu item.
            add_to_menu: <bool> True,
                Should this item be included in a menu.
            minimum_rank_required: <int> None 
                What is the user's minimum role rank to access the table
                or for it to be displayed in the menu
            roles: <list> []
                If the user does not have one or more of these roles assigned, 
                they will not have access to the table and it will not appear in
                the menu
        
        Example:
            Admin.register(TableObj,url,[,display_name=None[,minimum_rank_required=None[,roles=None]]])
            
            results in an item being added to self.permissions:
                self.permissions = [{table,display_name,url,minimum_rank_required(default = 99999999),roles(default = [])},]
        
        Registering a table again will replace the previous registration for that table.
        
        """
        
        display_name=kwargs.get('display_name',None)
        minimum_rank_required=kwargs.get('minimum_rank_required',99999999) #No one can access without a qualifiying role
        header_row = kwargs.get('header_row',False)
        top_level = kwargs.get('top_level',False)
        roles=kwargs.get('roles',[])
        if roles:
            roles = [x.lower() for x in roles ]
        add_to_menu = kwargs.get('add_to_menu',True)
        
        
        table_ref = table(self.db)
        if not display_name:
            display_name = table_ref.display_name
            
        permission = {'table':table,'display_name':display_name,'url':url,'header_row':header_row,'top_level':top_level,'minimum_rank_required':minimum_rank_required,'roles':roles,'add_to_menu':add_to_menu}
        
        #test that table only has one permission
        # as of 8/22/18 it is now the responsibilty of the developer to not duplicate permissions
        #for x in range(len(self.permissions)):
        #    if self.permissions[x]['table'] == table:
        #        self.permissions[x] = permission
        #        return
                
        self.permissions.append(permission)
           
    
    def has_user_table_access(self,user_name):
        """Special function to see if current user has access to the user table
        A shortcut I want to use in the menu template"""
        
        from shotglass2.users.models import User
        return self.has_access(user_name,User)
        
        
    def has_access(self,user_name,table=None):
        """Test to see if the user represented by user name has access to ANY admin items
        If a table class is specified, only check to see if user has access to that table
        
        If 'table' is a string, look for permissions by the display_name.
        Useful when testing the permissions from a template where the table object is not available.
        """
        from shotglass2.users.models import User
        
        if len(self.permissions) == 0:
            return False
            
        user = User(self.db)
        rec = user.get(user_name)
        if not rec or not user:
            return False
            
        user_roles = user.get_roles(rec.id)
        if not user_roles:
            return False
            
        temp_list = self.permissions
        if table:
            dict_item = 'table'
            try:
                if type(table) is str:
                    # Look up the table by display name
                    dict_item = 'display_name'
                    
                temp_list = [x for x in temp_list if x[dict_item] == table]
            except:
                return False

        for role in user_roles:
            for list_item in temp_list:
                if role.name.lower() in list_item['roles']:
                    return True
                if list_item['minimum_rank_required'] <= role.rank:
                    return True
                    
        return False
        

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Login Required")
            return redirect(url_for('login.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
    
def table_access_required(table):
    """A decorator that tests if the current user has sufficient privileges to access
    the table specified.
    
    If the user does not have sufficient access privileges the user is redirected 
    to the login.login with an appropreate message.
    
    Parameters
        table : Database table object
            The table to which the user must have access
        
    Returns
        Decorated function or redirect to login.login
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None or not g.admin or not g.admin.has_access(g.user,table):
                flash("Sorry. You do not have access to that page")
                return redirect(url_for('login.login', next=request.url))
            return f(*args,**kwargs)
        return decorated_function
    return decorator
    
    
def silent_login(alert=True):
    """A decorator to test that a user is logged in or
    log in a user without displaying the login page first.
    
    If the user is not logged in or if valid credentials are not in the request form
    redirect to the login.login page, else process the request
    
    Parameters
        alert : bool
            If True and login fails, Flash a failure message and email the system admin to
            inform admin of event.
    
    Returns
        Decorated function or redirect to login.login
        
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from shotglass2.users.views.login import authenticate_user
            from shotglass2.takeabeltof.mailer import email_admin
            if g.user == None \
                and (not request.form \
                or 'username' not in request.form \
                or 'password' not in request.form \
                or authenticate_user(request.form["username"],request.form['password']) != 1):
                if alert:
                    email_admin("Silent Login Failed","A attempt to login to {} silently failed".format(request.url))
                flash("Login Required")
                return redirect(url_for('login.login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
