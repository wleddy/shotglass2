from datetime import datetime
from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, session
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.mailer import send_message
from shotglass2.takeabeltof.utils import printException, cleanRecordID, looksLikeEmailAddress, render_markdown_for
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.users.models import User, Role, UserRole
from shotglass2.users.utils import get_access_token
from shotglass2.users.views.login import setUserStatus
from shotglass2.users.views.password import getPasswordHash

from time import time

USER_ROLES_SELECT_OBJ = "user_roles_select" #The ID of the role select html object
USER_STATUS_SELECT_OBJ = "user_status_select"

from shotglass2.takeabeltof.views import TableView
class UserView(TableView):
    def __init__(self,table,db,**kwargs):
        super().__init__(table,db,**kwargs)
        
        self.list_fields = [
            {'name':'id','label':'ID','class':'w3-hide-small','search':True},
            {'name':"full_name"},
            {'name':'email','class':'w3-hide-small'},
            {'name':'active','label':"Status",'class':'w3-hide-small'},
            {'name':'roles','list':False}
        ]
        
        self.export_fields = [
            {'name':'id'},
            {'name':'first_name'},
            {'name':'last_name'},
            {'name':'email'},
            {'name':'phone'},
            {'name':'address'},
            {'name':'address2'},
            {'name':'city'},
            {'name':'state'},
            {'name':'zip'},
            {'name':'username'},
            {'name':'active'},
            {'name':'may_send_email'},
            {'name':'may_send_text'},
            {'name':'last_access'},
            {'name':'roles'},
        ]
        
        # self.list_template = 'user_list.html'
        self.list_table_template = 'user_list_table.html'
        g.listURL = url_for('.display')
        g.adminURL = url_for('.admin',id=0)
        g.editURL = url_for('.edit')
        g.registerURL = url_for('.register')
        g.homeURL = '/'
        g.title = 'User'
        
        self.head = """<link rel="stylesheet" href="{}">""".format( url_for('static', filename='user/user_styles.css' ))
       
        """
        The User record list template includes some special query data that is added to the session
        to track the users role selections that need to be defined so they are passed with the python
        class object
        
        """
        self.USER_ROLES_SELECT_OBJ = USER_ROLES_SELECT_OBJ #The ID of the role select html object
        self.list_search_widget_extras_template = "user_search_widget_extras.html"
        # Will need all the roles to list
        self.user_roles = Role(self.db).select()
        
        #track if user wants active or inactive records listed
        self.USER_STATUS_SELECT_OBJ = USER_STATUS_SELECT_OBJ
        
    def delete(self,*args,**kwargs):
        record_id = None
        delete_by_admin = request.args.get('delete',None)
        if delete_by_admin:
            rec=self.table.select_one(where='access_token = "{}"'.format(delete_by_admin.strip()))
            if rec:
                record_id = rec.id

        if not record_id and len(self.path) > 1:
            record_id = self.path[1]
    
        self.success = self.table.delete(cleanRecordID(record_id))
        
        if not self.success:
            self.result_text = 'Not able to delete that record.'
        else:
            self.db.commit()
            self.result_text = 'User Record Deleted'
            
        flash(self.result_text)

           
    def select_recs(self,**kwargs):
        """Override the default record selection method for lists"""
        # import pdb;pdb.set_trace()
        
        # get user status requested
        kwargs.update({'user_status_select':session.get(self.USER_STATUS_SELECT_OBJ,"-1"),'user_rank':self.table.max_role_rank(g.user)})
        super().select_recs(**kwargs)
        
        if not self.recs:
            return
            
        """The user list has a potential to limit the selection by user's role(s)
        
        After running the normal search, loop through the found records and delete any without the 
        requested roles
        
        """

        user_role_id_list = session.get(self.USER_ROLES_SELECT_OBJ)
        if not user_role_id_list or 0 in user_role_id_list:
            return
            
        user_role_id_list = ','.join(str(x) for x in user_role_id_list)
        
        for x in range(len(self.recs)-1,-1,-1): # turkey shoot loop
            user_role_rec = UserRole(self.db).select_one(where="user_id = {} and role_id in ({})".format(self.recs[x].id,user_role_id_list))
            if not user_role_rec:
                del self.recs[x]
        
        
mod = Blueprint('user',__name__, template_folder='templates/user', url_prefix='/user', static_folder="static")



@mod.route('/save_table_search',methods=['POST'])
@mod.route('/save_table_search/',methods=['POST'])
def save_table_search():
    """Save the table search string and column to the sesstion"""
    
    # import pdb;pdb.set_trace()
    
    d = {}
    if request.form:
        # request form is immutable, so move to simple dict
        for key in request.form.keys():
            d[key] = request.form[key]
    
    if 'table_search' not in session:
        session['table_search'] = {}
        
    search_table_name = d.pop('search_table_name')
    save_search = d.get('save_search','false') # this is JS true|false as text
    if save_search == 'true' and search_table_name:
        session['table_search'].update({search_table_name: d})
    elif save_search == 'false' and search_table_name:
        try:
            del session['table_search'][search_table_name]
        except:
            pass

    return ''
            

def setExits():
    g.listURL = url_for('.display')
    g.adminURL = url_for('.admin',id=0)
    g.editURL = url_for('.edit')
    g.registerURL = url_for('.register')
    g.deleteURL = url_for('.display') + "delete/"
    g.homeURL = '/'
    g.title = 'User'

#@mod.route('/')
def home():
    setExits()
    if g.user:
        return redirect(g.listURL)
        
    return redirect('/')
    
@mod.route('/<path:path>',methods=['GET','POST',])
@mod.route('/<path:path>/',methods=['GET','POST',])
@mod.route('/',methods=['GET','POST',])
@table_access_required(User)
def display(path=""):
    setExits()
    g.title = "{} Record List".format(g.title)
    user = User(g.db)
    user_rank = user.max_role_rank(g.user)
    user_list = UserView(User,g.db)
    return user_list.dispatch_request(include_inactive=True,user_rank=user_rank)
            
    
@mod.route('/edit/<int:id>/', methods=['POST','GET'])
@table_access_required(User)
def admin(id=None):
    """Administrator access for the User table records
    """
    setExits()
    if id == None:
        flash("No User identifier supplied")
        return redirect(g.listURL)
        
    #import pdb;pdb.set_trace()
        
    id = cleanRecordID(id)
    if(id < 0):
        flash("That is an invalid id")
        return redirect(g.listURL)
        
    #session['user_edit_token'] = id
    
    return edit(id)
    

## Edit the user
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
@login_required
def edit(rec_handle=None):
    setExits()
    g.title = "Edit {} Record".format(g.title)
    #import pdb;pdb.set_trace()
    site_config = get_site_config()
    
    user = User(g.db)
    rec = None
    request_rec_id = cleanRecordID(request.form.get('id',request.args.get('id',-1)))
    is_admin = g.admin.has_access(g.user,User)
    no_delete = not is_admin
    new_password = ''
    confirm_password = ''
    user_roles = ['user'] # default
        
    #limit roles to roles <= current users rank
    curr_user_max_rank = user.max_role_rank(g.user)
    roles = Role(g.db).select(where="rank <= {}".format(curr_user_max_rank))
        
    include_inactive = True
    next = request.form.get('next',request.args.get('next',''))
    
    if not is_admin:
        g.listURL = g.homeURL # Non admins can't see the list
        include_inactive = False
        
    if rec_handle != None:
        pass #rec_handle has to come from admin() at this point
    elif rec_handle == None and g.user != None and request_rec_id == -1:
        rec_handle = g.user
    else:
        rec_handle = request_rec_id
        if rec_handle < 0:
            flash("That is not a valid User ID")
            return redirect(g.listURL)
        
    if not request.form:
        """ if no form object, send the form page """
        if rec_handle != g.user and not is_admin:
            flash("You do not have access to that area")
            return redirect(g.homeURL)
        elif curr_user_max_rank < user.max_role_rank(rec_handle):
            flash("You don't have sufficiant privelages to edit that user record.")
            return redirect(g.homeURL)
        elif rec_handle == 0:
            rec = user.new()
        else:
            rec = user.get(rec_handle,include_inactive=include_inactive)
            if not rec:
                flash("Unable to locate user record")
                return redirect('/')
            
            user_roles = get_user_role_names(rec)
        
    else:
        #have the request form
        #import pdb;pdb.set_trace()
        is_new_user = False
        if rec_handle and request.form['id'] != 'None':
            rec = user.get(rec_handle,include_inactive=include_inactive)
            user_roles = get_user_role_names(rec)
        else:
            # its a new unsaved record
            is_new_user = True
            rec = user.new()
            user.update(rec,request.form)

        if validForm(rec):
        
            #Are we editing the current user's record?
            editingCurrentUser = ''
            if(g.user == rec.username):
                if 'new_username' in request.form:
                    editingCurrentUser = request.form['new_username'].strip()
                else:
                    editingCurrentUser = g.user
            else: 
                if(g.user == rec.email):
                    editingCurrentUser = request.form['email'].strip()
            
            #update the record
            user.update(rec,request.form)
                
            # ensure these are ints
            if 'may_send_email' in rec._fields:
                rec.may_send_email = cleanRecordID(rec.may_send_email)
            if 'may_send_text' in rec._fields:
                rec.may_send_text = cleanRecordID(rec.may_send_text)
            
            set_username_from_form(rec)        
            set_password_from_form(rec)
    
            try:
                user.save(rec)
                
                # update the user roles
                if 'roles_select' in request.form:
                    # import pdb;pdb.set_trace()
                    #delete all the users current roles
                    user.clear_roles(rec.id)
                    for role_name in request.form.getlist('roles_select'):
                        #find the role by name
                        role = Role(g.db).select_one(where='name = "{}"'.format(role_name))
                        if role:
                            user.add_role(rec.id,role.id)
                    
                # if the username or email address are the same as g.user
                # update g.user if it changes
                if(editingCurrentUser != ''):
                    setUserStatus(editingCurrentUser,rec.id)
                    
                g.db.commit()
                
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))
                return redirect(g.listURL)
                
            if is_new_user == True and rec.email:
                
                # send an email to welcome the new user
                full_name = '{} {}'.format(rec.first_name,rec.last_name).strip()
                
                context = {'rec':rec,'full_name':full_name,}
                to_address_list=[(full_name,rec.email)]
                sent,msg = send_message(
                    to_address_list,
                    subject="Welcome to {{ site_config.SITE_NAME}}",
                    context=context,
                    html_template='email/welcome.html',
                    text_template='email/welcome.txt',
                    )
                if not sent:
                    flash('The welcome message could not be sent. Error: {}'.format(msg))
                    
            return redirect(g.listURL)
        
        else:
            # form did not validate, give user the option to keep their old password if there was one
            #need to restore the username
            user.update(rec,request.form)
            if 'new_username' in request.form:
                rec.username = request.form['new_username'] #preserve user input
            # preserve the selected roles
            #import pdb;pdb.set_trace()
            if 'roles_select' in request.form:
                user_roles = request.form.getlist('roles_select')
            #and password
            new_password = request.form.get('new_password','')
            confirm_password = request.form.get('confirm_password','')

    # display form
    return render_template('user_edit.html', 
        rec=rec, 
        no_delete=no_delete, 
        is_admin=is_admin,
        next=next,
        user_roles=user_roles, 
        roles=roles,
        new_password=new_password,
        confirm_password=confirm_password,
        )
    
@mod.route('/register', methods=['GET','POST',])
@mod.route('/register/', methods=['GET','POST',])
def register():
    """Allow people to sign up thier own accounts on the web site"""
    setExits()
    site_config = get_site_config()
    
    g.title = "Account Registration"
    g.editURL = url_for('.register')
    g.listURL = '/' # incase user cancels
    user = User(g.db)
    rec=user.new()
    
    is_admin = False
    user_roles=None
    roles=None
    no_delete=True
    success=True
    help = render_markdown_for("new_account_help.md",mod)  
    next = request.form.get('next',request.args.get('next',''))     
    
    if 'confirm' in request.args:
        #Try to find the user record that requested registration
        rec=user.select_one(where='access_token = "{}"'.format(request.args.get('confirm','')).strip())
        if rec and rec.access_token_expires > time():
            if site_config.get('ACTIVATE_USER_ON_CONFIRMATION',False):
                rec.active = 1 
                user.save(rec,commit=True)
                # log the user in
                setUserStatus(rec.email,rec.id)
                
            if rec.active == 1:
                success="active"
            else:
                success="waiting"
                
            #inform the admin
            to=[(site_config['MAIL_DEFAULT_SENDER'],site_config['MAIL_DEFAULT_ADDR'])]
            confirmURL = "{}://{}{}?activate={}".format(site_config['HOST_PROTOCOL'],site_config['HOST_NAME'],url_for('.activate'), rec.access_token)
            deleteURL = "{}://{}{}?delete={}".format(site_config['HOST_PROTOCOL'],site_config['HOST_NAME'],url_for('.delete'), rec.access_token)
            context={'rec':rec,'confirmURL':confirmURL,'deleteURL':deleteURL}
            subject = 'Activate Account Request from - {}'.format(site_config['SITE_NAME'])
            html_template = 'email/admin_activate_acct.html'
            text_template = None
            send_message(to,context=context,subject=subject,html_template=html_template,text_template=text_template)
            
            return render_template('registration_success.html',success=success,next=next)
        else:
            flash("That registration request has expired")
            return redirect('/')

    if not request.form:
        pass
    else:
        if validForm(rec):
            #update the record
            user.update(rec,request.form)
            rec.active = 0 # Self registered accounts are inactive by default
            set_password_from_form(rec)
            set_username_from_form(rec)
            rec.access_token = get_access_token()
            rec.access_token_expires = time() + (3600 * 48)
            if site_config.get('AUTOMATICALLY_ACTIVATE_NEW_USERS',False):
                rec.active = 1
                success="active"
            try:
                user.save(rec)
                
                # give user default roles
                for role in site_config.get('DEFAULT_USER_ROLES',['user']):
                    User(g.db).add_role(rec.id,role)
            
                g.db.commit()
                # log the user in
                setUserStatus(rec.email,rec.id)
                
                #Send confirmation email to user if not already active
                full_name = '{} {}'.format(rec.first_name,rec.last_name).strip()
                to=[(full_name,rec.email)]
                context={'rec':rec,'confirmation_code':rec.access_token}
                subject = 'Please confirm your account registration at {}'.format(site_config['SITE_NAME'])
                html_template = 'email/registration_confirm.html'
                text_template = 'email/registration_confirm.txt'
                if rec.active == 1:
                    subject = 'Your account is now active at {}'.format(site_config['SITE_NAME'])
                    html_template = 'email/activation_complete.html'
                    text_template = 'email/activation_complete.txt'
                    
                send_message(to,context=context,subject=subject,html_template=html_template,text_template=text_template)
                
                #inform the admin
                to=[(site_config['MAIL_DEFAULT_SENDER'],site_config['MAIL_DEFAULT_ADDR'])]
                deleteURL = "{}://{}{}?delete={}".format(site_config['HOST_PROTOCOL'],site_config['HOST_NAME'],g.deleteURL, rec.access_token)
                editURL = "{}://{}{}{}".format(site_config['HOST_PROTOCOL'],site_config['HOST_NAME'],url_for('.edit'), rec.id)
                context={'rec':rec,'deleteURL':deleteURL,'editURL':editURL,'registration_exp':datetime.fromtimestamp(rec.access_token_expires).strftime('%Y-%m-%d %H:%M:%S')}
                subject = 'Unconfirmed Account Request from - {}'.format(site_config['SITE_NAME'])
                if site_config.get('AUTOMATICALLY_ACTIVATE_NEW_USERS',True):
                    subject = 'New Account Auto Activated - {}'.format(site_config['SITE_NAME'])
                html_template = 'email/admin_activate_acct.html'
                text_template = None
                send_message(to,context=context,subject=subject,html_template=html_template,text_template=text_template)


            except Exception as e:
                g.db.rollback()
                mes = "An error occured while new user was attempting to register"
                printException(mes,"error",e)
                # Send email to the administrator
                to=[(site_config['MAIL_DEFAULT_SENDER'],site_config['MAIL_DEFAULT_ADDR'])]
                context={'mes':mes,'rec':rec,'e':str(e)}
                body = "Signup Error\n{{context.mes}}\n{{context.e}}\nrec:\n{{context.rec}}"
                send_message(to,context=context,body=body,subject=mes)
                success = False
            
            return render_template('registration_success.html',success=success,next=next,)
        else:
            #validation failed
            user.update(rec,request.form)
            
    return render_template('user_edit.html',
        rec=rec, 
        no_delete=no_delete, 
        is_admin=is_admin,
        next=next,
        )
        

@mod.route('/activate/', methods=['GET'])
@table_access_required(User)
def activate():
    """Allow administrator to activate a new user"""
    
    activate = request.args.get('activate',None)
    if activate:
        user = User(g.db)
        rec=user.select_one(where='access_token = "{}"'.format(activate.strip()))
        if rec:
            rec.active = 1
            rec.access_token = None
            rec.access_token_expires = None
            user.save(rec)
            g.db.commit()
            
            # inform user that their account is now active
            full_name = '{} {}'.format(rec.first_name,rec.last_name).strip()
            to=[(full_name,rec.email)]
            context={'rec':rec,}
            subject = 'Account Activated'
            html_template = 'email/activation_complete.html'
            text_template = 'email/activation_complete.txt'
            send_message(to,context=context,subject=subject,html_template=html_template,text_template=text_template)
            
        else:
            flash("User not found with access_token: {}".format(activate))
            return redirect('/')
            
    else:
        flash("Activation code not in request args")
        return redirect('/')
    
    flash("New User Activation Successful")
    return edit(rec.id)


@mod.route('/set_list_roles', methods=['POST'])
@mod.route('/set_list_roles/', methods=['POST'])
@table_access_required(User)
def set_list_roles():
    """Record the selected roles for the user list page"""
    # import pdb;pdb.set_trace()
    element_name = USER_ROLES_SELECT_OBJ
    if element_name not in request.form:
        element_name = element_name + "[]" # brackets may be added by jquery or because it's an ajax post?
        
    selected_values = request.form.getlist(element_name)
        
    session[USER_ROLES_SELECT_OBJ] = []
    
    # Use the long form loop in case any of the values submitted do not evalutate with int()
    if selected_values and isinstance(selected_values,list):
        for x in selected_values:
            try:
                session[USER_ROLES_SELECT_OBJ].append(int(x))
            except:
                printException("Error in user.py.set_list_roles. bad value for USER_ROLES_SELECT_OBJ. -> '{}'".format(x))
            
    return "OK"
    
    
@mod.route('/set_list_status', methods=['POST'])
@mod.route('/set_list_status/', methods=['POST'])
@table_access_required(User)
def set_list_status():
    """Record the selected roles for the user list page"""
    # import pdb;pdb.set_trace()
    session[USER_STATUS_SELECT_OBJ] = request.form.get(USER_STATUS_SELECT_OBJ,"-1")
        
    return "OK"


def validForm(rec):
    # Validate the form
    goodForm = True
    user = User(g.db)
    
    if request.form['email'].strip() == '':
        goodForm = False
        flash('Email may not be blank')

    if request.form['email'].strip() != '' and not looksLikeEmailAddress(request.form['email'].strip()):
        goodForm = False
        flash("That doesn't look like a valid email address")

    if request.form['email'].strip() != '':
        # always test lower case version of email
        found = user.get(request.form['email'].strip().lower(),include_inactive=True)
        if found:
            if request.form['id'] == 'None' or found.id != int(request.form['id']):
                goodForm = False
                flash('That email address is already in use')
            
    # user name must be unique if supplied
    if 'new_username' in request.form:
        if request.form['new_username'].strip() != '':
            found = user.get(request.form['new_username'].strip(),include_inactive=True)
            if found:
                if request.form['id'] == 'None' or found.id != int(request.form['id']):
                    goodForm = False
                    flash('That User Name is already in use')
        
        if request.form["new_username"].strip() != '' and request.form["new_password"].strip() == '' and rec.password == '':
            goodForm = False
            flash('There must be a password if there is a User Name')
        
    if request.form["new_password"].strip() == '' and request.form["confirm_password"].strip() != '' and rec.password != '':
        goodForm = False
        flash("You can't enter a blank password.")
    
    #passwords must match if present
    if request.form['confirm_password'].strip() != request.form['new_password'].strip():
        goodForm = False
        flash('Passwords don\'t match.')
        
    return goodForm
    
def get_user_role_names(rec):
    user_roles = []
    roles = User(g.db).get_roles(rec.id)
    if roles:
        for x in roles:
            user_roles.append(x.name)
            
    return user_roles
    
def set_password_from_form(rec):
    if not request.form['new_password'] or (rec.password != None and request.form['new_password'].strip() == ''):
        # Don't change the password
        pass
    else:
        user_password = ''
        if request.form['new_password'].strip() != '':
            user_password = getPasswordHash(request.form['new_password'].strip())
            rec.access_token = None
            rec.access_token_expires = None

        if user_password != '':
            rec.password = user_password
        else:
            rec.password = None
    
def set_username_from_form(rec):
    user_name = ''
    if 'new_username' in request.form:
        user_name = request.form['new_username'].strip()
    
        if user_name != '':
            rec.username = user_name
        else:
            rec.username = None
    
