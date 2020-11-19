from flask import request, session, g, redirect, url_for, \
     render_template, flash, Blueprint
from shotglass2.users.models import Pref
from shotglass2.takeabeltof.utils import printException, cleanRecordID
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.takeabeltof.views import TableView
mod = Blueprint('pref',__name__, template_folder='templates/pref', url_prefix='/pref')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.display') + 'delete/'
    g.title = 'Preferences'

@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(Pref)
def display(path=None):
    setExits()
    g.title = "{} Record List".format(g.title)
    view = TableView(Pref,g.db)
    view.list_fields = [
        {'name':'id','label':'ID','class':'w3-hide-small','search':True},
        {'name':"name"},
        {'name':"value"},
        {'name':"expires",'type':'date','default':'-- Never --'},
        {'name':"user_name",'class':'w3-hide-small','default':'-- All --'},
    ]
        
    return view.dispatch_request()
    

## Edit the Pref
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@mod.route('/edit/<int:rec_id>/', methods=['POST','GET'])
@table_access_required(Pref)
def edit(rec_id=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)

    pref = Pref(g.db)
    rec = None
    
    if rec_id == None:
        rec_id = request.form.get('id',request.args.get('id',-1))
        
    rec_id = cleanRecordID(rec_id)
    #import pdb;pdb.set_trace

    if rec_id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
        
    if not request.form:
        """ if no form object, send the form page """
        if rec_id == 0:
            rec = pref.new()
        else:
            rec = pref.get(rec_id)
            if not rec:
                flash("Unable to locate that record")
                return redirect(g.listURL)
    else:
        #have the request form
        #import pdb;pdb.set_trace()
        if rec_id and request.form['id'] != 'None':
            rec = pref.get(rec_id)
        else:
            # its a new unsaved record
            rec = pref.new()
            pref.update(rec,request.form)

        if validForm(rec):
            #update the record
            #import pdb;pdb.set_trace()
            
            pref.update(rec,request.form)
            # make names lower case
            if rec.user_name.strip() == '':
                rec.user_name = None
            if rec.expires and rec.expires.strip().lower() == 'never':
                rec.expires = None
                
            try:
                pref.save(rec)
                g.db.commit()
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))

            return redirect(g.listURL)
        
        else:
            # form did not validate
            pass

    # display form
    return render_template('pref_edit.html', rec=rec)
    
    
def validForm(rec):
    # Validate the form
    goodForm = True
    #import pdb;pdb.set_trace()
    if request.form['name'].strip() == '':
        goodForm = False
        flash('Name may not be blank')
    else:
        # name must be unique for each user
        #"select from pref where name = rec.name and id <> rec.id and user_name = rec.user_name or Null"
        where = 'name="{}"'.format(request.form['name'].strip(),)
        if rec.id:
            where += ' and id <> {} '.format(rec.id)
        if rec.user_name:
            where += ' and user_name = "{}"'.format(rec.user_name.strip())
        else:
            where += ' and user_name is null'
            
        if Pref(g.db).select(
            where=where
            ) != None:
            goodForm = False
            flash('Pref names must be unique')
                
    return goodForm
    
    
def get_contact_email():
    """Return a tuple of the contact name and email address or None"""
    from shotglass2.shotglass import get_site_config
    
    site_config = get_site_config()
    
    to = None
    to_name = None
    to_addr = None
    
    rec = Pref(g.db).get("Contact Name",user_name=site_config.get("HOST_NAME"),default=site_config.get("CONTACT_NAME",site_config.get("MAIL_DEFAULT_SENDER","Site Contact")))
    if rec:
        to_name = rec.value
    rec = Pref(g.db).get("Contact Email Address",user_name=site_config.get("HOST_NAME"),
            default=site_config.get("CONTACT_EMAIL_ADDR",
                        site_config.get("MAIL_DEFAULT_ADDR","info@{}".format(site_config.get("HOST_NAME","example.com")))))
    if rec:
        to_addr = rec.value
                    
    to = (to_name,to_addr,)
        
    return to
