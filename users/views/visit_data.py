from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.users.models import VisitData
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.views import TableView

mod = Blueprint('visit_data',__name__, template_folder='templates/visit_data', url_prefix='/visit_data')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.display')
    g.deleteURL = url_for('.display')
    g.title = 'Visit Data'

@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(VisitData)
def display(path=None):
    setExits()
    g.title = "{} Record List".format(g.title)
    view = TableView(VisitData,g.db)
    view.allow_record_addition = False
        
    return view.dispatch_request()
    