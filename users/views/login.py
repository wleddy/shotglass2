from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import sleep, time
import random
from shotglass2.users.models import User
from shotglass2.users.views.password import getPasswordHash, matchPasswordToHash
from shotglass2.users.utils import get_access_token
from shotglass2.users.admin import silent_login

mod = Blueprint('login',__name__, template_folder='templates/login')


def setExits():
    g.title = 'Login'
    g.loginURL = url_for('.login')
    g.recoverURL = url_for('.recover_password')
    g.logoutURL = url_for('.logout')
    g.registerURL = url_for('user.register')
    
@mod.route('/login', methods=['POST', 'GET'])
@mod.route('/login/', methods=['POST', 'GET'])
def login():
    setExits()
    g.user = g.get('user',None)
    next = request.args.get('next',request.form.get('next',''))
    get_pass=request.form.get('get_pass',False)
    
    if g.user is not None:
        #flash("Already Logged in...")
        return redirect('/')
        
    if 'reset' in request.args:
        #Try to find the user record that requested a reset
        rec=User(g.db).select_one(where='access_token = "{}"'.format(request.args.get('reset','')).strip())
        if rec and rec.access_token_expires > time():
            userNameOrEmail=rec.username
            if not userNameOrEmail:
                userNameOrEmail=rec.email
            setUserStatus(userNameOrEmail,rec.id)
            return redirect(url_for('user.edit'))
        else:
            flash("That reset request has expired")
            return redirect('/')
            
    if not request.form:
        if 'loginTries' not in session:
            session['loginTries'] = 0
        
    if request.form:
        if 'loginTries' not in session:
            #Testing that user agent is keeping cookies.
            #If not, there is no point in going on... Also, could be a bot.
            return render_template('no-cookies.html')
        
        result = authenticate_user(request.form["userNameOrEmail"],request.form.get('password'))
        if result ==2:
            # need to get password from user
            get_pass=True
        elif result != 0:
            session['loginTries'] = 0
            if result == -1:
                flash("Your account is inactive")
                return render_template('inactive.html')
            #import pdb;pdb.set_trace()          
            if next:
                return redirect(next)
            return redirect('/') #logged in...
        else:
            flash("Invalid User Name or Password")
        
    if 'loginTries' not in session:
        session['loginTries'] = 0
        
    #remember howmany times the user has tried to log in
    session['loginTries'] = session['loginTries'] + 1
    #slow down login attempts
    if session['loginTries'] > 5:
        sleep(session['loginTries']/.8)
        
    return render_template('login.html', form=request.form, next=next, get_pass=get_pass)
       
    
@mod.route('/logout', methods=['GET'])
@mod.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    g.user = None
    #flash("Successfully Logged Out")
    return redirect('/')
    
@mod.route('/reset', methods=['GET','POST'])
@mod.route('/reset/', methods=['GET','POST'])
def recover_password():
    """Send reset password and send user an email if they forget their password"""
    
    setExits()
    g.title = "Reset Password"
    rec=None
    temp_pass = None
    email_not_found = False
    
    if not request.form:
        pass
    else:
        #find the user with that email
        rec = User(g.db).select_one(where='lower(email) = lower("{}")'.format(request.form['email'].strip().lower()))
        if rec == None:
            flash("That email address could not be found in the list of users.")
        else:
            # generate a new password that is unique to the system
            temp_pass = get_access_token()
            # save the temporary password
            rec.access_token = temp_pass
            rec.access_token_expires = time() + (3600 * 48) # 2 days to reset
            User(g.db).save(rec)
            g.db.commit()
            
            # send an email with instructions
            from shotglass2.takeabeltof.mailer import send_message
            full_name = rec.first_name + " " + rec.last_name
            context = {'temp_pass':temp_pass,'rec':rec,'full_name':full_name}
            to_address_list=[(full_name,rec.email),]
            result,msg = send_message(
                to_address_list,
                context=context,
                html_template='email/confirm_reset.html',
                text_template='email/confirm_reset.txt',
                subject = 'Confirm Password Reset'
                )
    
    # Return a page telling user what we did
    return render_template('recover_password.html',temp_pass=temp_pass,rec=rec)
    
    
@mod.route('/quiet_test', methods=['GET','POST'])
@mod.route('/quiet_test/', methods=['GET','POST'])
@silent_login()
def quite_test_fixture():
    """Simple way to test that the silent_login decorator is working"""
    return "Ok"
    
    
def setUserStatus(userNameOrEmail,user_id):
    #Log the user in
    user = User(g.db)
    rec = user.get(user_id)
    if rec:
        user.update_last_access(rec.id)
        session["user"] = userNameOrEmail.strip()
        session['user_id'] = rec.id
        g.user = session["user"]
        session["user_roles"] = []
        recs = user.get_roles(rec.id)
        if recs:
            session["user_roles"] = [rec.name for rec in recs]
        g.user_roles = session['user_roles']
        g.user_has_password = session['user_has_password'] = (rec.password != None and rec.password != '')
    else:
        flash("Unable to locate user")
    
    
def authenticate_user(username,password,**kwargs):
    """
    Check username and password in db and return:
        0 = Authentication Failed
        1 = Authentication Succeeded
        2 = Need a password for this user
        -1 = User Inactive
        
    Optional kwargs:
        include_inactive = True
        login_on_success = True
    """
    
    include_inactive = kwargs.get('include_inactive',True)
    login_on_success = kwargs.get('login_on_success',True)
    
    result = 0
    
    #import pdb; pdb.set_trace()
    
    rec = User(g.db).get(username,include_inactive=include_inactive)
    
    if rec:
        if not rec.password:
            #User has no password, just login
            result = 1
        elif not password:
            #need a password for this user
            result = 2
        elif matchPasswordToHash(password,rec.password):
            result = 1
        if rec.active != 1:
            result = -1
        if result == 1 and rec.active == 1 and login_on_success:
            # use rec.username if there is one
            if rec.username:
                username = rec.username
            setUserStatus(username,rec.id)
            
    return result
            

    
    
