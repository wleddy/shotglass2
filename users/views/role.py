from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.users.models import Role, User
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.takeabeltof.views import TableView, ListFilter
from shotglass2.users.admin import login_required, table_access_required

mod = Blueprint('role',__name__, template_folder='templates/role', url_prefix='/role')

PRIMARY_TABLE = Role

class RoleTableView(TableView):
    def __init__(self,table,db,**kwargs):
        super().__init__(table,db,**kwargs)
        self.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-small','search':True,},
            {'name':'name',},
            {'name':'description'},
            {'name':'rank'},
        ]


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Role'

@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(PRIMARY_TABLE)
def display(path=None):    
    return RoleTableView(PRIMARY_TABLE,g.db).dispatch_request()
    
    

# Edit the role
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@table_access_required(PRIMARY_TABLE)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    role = PRIMARY_TABLE(g.db)
    rec = None
    super_user = User(g.db).user_has_role(session['user_id'],'Super')
    
    rec_id = cleanRecordID(request.form.get('id',rec_id))
    
    
    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    if not request.form:
        """ if no form object, send the form page """
        if rec_id == 0:
            rec = role.new()
        else:
            rec = role.get(rec_id)
            if not rec:
                flash("Unable to locate that record")
                return redirect(g.listURL)
    else:
        #have the request form
        if rec_id and request.form['id'] != 'None':
            rec = role.get(rec_id)
        else:
            # its a new unsaved record
            rec = role.new()
            role.update(rec,request.form)

        if validForm(rec):
            #update the record
            #import pdb;pdb.set_trace()
            role.update(rec,request.form)
            # locked is a checkbox
            if 'locked' in request.form:
                rec.locked = 1
            else:
                rec.locked = 0
            
            try:
                role.save(rec)
                g.db.commit()
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))

            return redirect(g.listURL)
        
        else:
            # form did not validate
            pass

    # display form
    return render_template('role_edit.html', rec=rec,super_user=super_user,no_delete=not super_user)
    
    
def validForm(rec):
    # Validate the form
    goodForm = True
    
    if request.form['name'].strip() == '':
        goodForm = False
        flash('Name may not be blank')
    else:
        # name must be unique (but not case sensitive)
        where = 'lower(name)="{}"'.format(request.form['name'].lower().strip(),)
        if rec.id:
            where += ' and id <> {}'.format(rec.id)
        if PRIMARY_TABLE(g.db).select(
            where=where
            ) != None:
            goodForm = False
            flash('Role names must be unique')
        
    # Rank must be in a reasonalble range
    temp_rank = cleanRecordID(request.form['rank'])
    if temp_rank < 0 or temp_rank > 1000:
        goodForm = False
        flash("The Rank must be between 0 and 1000")
        
    return goodForm
    

