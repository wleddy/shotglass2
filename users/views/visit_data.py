from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.users.models import VisitData
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.views import TableView, EditView

mod = Blueprint('visit_data',__name__, template_folder='templates/visit_data', url_prefix='/visit_data')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + '/delete/'
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
    

@mod.route('/edit/<int:rec_id>',methods=['GET','POST',])
@mod.route('/edit/<int:rec_id>/',methods=['GET','POST',])
@mod.route('/edit/',methods=['GET','POST',])
@table_access_required(VisitData)
def edit(rec_id=-1) ->str:
    setExits()
    rec_id = cleanRecordID(rec_id)
    if rec_id < 1:
        return redirect(g.listURL)
    
    editor = EditView(VisitData,g.db,rec_id=rec_id,edit_fields = [
        {'name': 'session_id','extras':'readonly','req':True},
        {'name':'user_name',},
        {'name':'value','type':'textarea',},
        {'name':'expires','type':'datetime'},
    ]
    )

    return editor.render()