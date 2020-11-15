from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.shotglass import ShotLog

mod = Blueprint('tools',__name__, template_folder='templates/', url_prefix='/tools')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Tools'

@mod.route('/view_log',methods=['GET',])
@mod.route('/view_log/',methods=['GET',])
@login_required
def view_log():
    """dump the log file to the screen"""
    g.title = "View Log"
    log = ShotLog().get_text() #log is a generator
    
    return render_template('log_viewer.html',log=log)
    
