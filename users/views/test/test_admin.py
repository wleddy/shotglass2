import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

from shotglass2.users.admin import Admin, login_required, table_access_required
import app
from shotglass2.users.models import User,Role
import os
import pytest

    
filespec = 'instance/test_admin.db'

db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)

        
def delete_test_db():
        os.remove(filespec)
                
def test_admin():
   admin = Admin(db)
   admin.register(User,'/user/',display_name='Users',minimum_rank_required=500,roles=['admin',])
   admin.register(Role,'/role/',display_name='User Permissions',minimum_rank_required=2000)
   assert len(admin.permissions) == 2
   #test the values
   assert admin.permissions[0]['display_name'] == 'Users'
   assert admin.permissions[0]['table'] == User
   assert admin.permissions[0]['url'] == '/user/'
   assert admin.permissions[0]['minimum_rank_required'] == 500
   assert admin.permissions[0]['roles'] == ['admin',]
   assert admin.permissions[0]['header_row'] == False
   assert admin.permissions[0]['top_level'] == False
   assert admin.permissions[0]['add_to_menu'] == True
   
   assert admin.has_access('admin') == True
   assert admin.has_access('admin',User) == True
   assert admin.has_access('admin',Role) == False
   assert admin.has_access('bleddy') == False
   assert admin.has_access('bleddy',User) == False
   assert admin.has_access('') == False
    
    
############################ The final 'test' ########################
######################################################################

def test_finished():
   try:
       db.close()
       delete_test_db()
       assert True
   except:
       assert True
