from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint, Response
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.users.models import User
from shotglass2.shotglass import ShotLog

mod = Blueprint('tools',__name__, template_folder='templates/', url_prefix='/tools')

def register_admin():
    if not g.admin:
        g.admin = Admin(g.db) # This is where user access rules are stored
    g.admin.register(User,
            '',
            display_name='Tools',
            minimum_rank_required=500,
            header_row=True
        )
    g.admin.register(User,
            url_for('tools.view_log'),
            display_name='View Log',
            minimum_rank_required=500,
        )
        
    
@mod.route('/view_log',methods=['GET',])
@mod.route('/view_log/',methods=['GET',])
@login_required
def view_log():
    """dump the log file to the screen"""
    g.title = "View Log"
    log = ShotLog().get_text() #log is a generator
    
    return render_template('log_viewer.html',log=log)
    

