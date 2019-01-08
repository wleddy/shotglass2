from flask import render_template, g, url_for, request, flash
from flask_mail import Mail
from shotglass2.takeabeltof.utils import send_static_file
from shotglass2.users.models import User,Role,Pref
from shotglass2.users.admin import Admin
import os    

def init_db(db=None):
    # to support old code
    initalize_all_tables(db)

def initalize_user_tables(db):
    """Initialize the Users, Prefs and Roles tables"""
        
    from shotglass2.users.models import init_db as users_init_db 
    users_init_db(db)
    
        
def get_app_config(this_app=None):
    """Returns a copy of the current app.config.
    This makes it possible for other modules to get access to the config
    with the values as updated for the current host.
    Import this method rather than importing app

    When called from app.py, the app is passed in. When
    called from other modules it is not needed.
    If not passed from app.py there seems to be some pieces
    missing and the template loader won't work correctly.
    In particular, it seems to be unable to find included templates.
    """
    import jinja2
   
    
    if not this_app:
        from app import app
        this_app = app
        
    #import pdb;pdb.set_trace()

    # if there is no request this function will error out
    # check to see if the property we need is available
    request_in_flight = True
    try:
        request.url
    except:
        request_in_flight = False

    if request_in_flight and "SUB_DOMAIN_SETTINGS" in this_app.config and len(this_app.config["SUB_DOMAIN_SETTINGS"]) > 0:
        try:
            server = None
            for value in this_app.config['SUB_DOMAIN_SETTINGS']:
                if value.get('host_name') == request.host:
                    server = value
                    break

            if not server:
                #did not find a server to match, use default
                raise ValueError

            for key, value in server.items():
                this_app.config[key.upper()] = value

            # refresh mail since settings changed
            from app import mail
            mail = Mail(this_app)

        except:
            # Will use the default settings
            if this_app.config['DEBUG']:
                #raise ValueError("SUB_DOMAIN_SETTINGS could not be determined")
             flash("Using Default SUB_DOMAIN_SETTINGS")
    
    #update the jinja loader
    template_dirs = this_app.config.get('TEMPLATE_DIRS')
    host_template_dirs = []
    if template_dirs:
        if isinstance(template_dirs,list):
            host_dir = this_app.config.get('HOST_TEMPLATE_DIRS',[])
            if host_dir:
                if isinstance(host_dir,list):
                    for j in range(len(host_dir)):
                        host_template_dirs.append(host_dir[j])
                        for i in range(len(template_dirs)):
                            host_template_dirs.append(os.path.join(host_dir[j],template_dirs[i]))
                else:
                    flash("app config 'HOST_TEMPLATE_DIRS' must be a list.")
                    
                    
            # generate a completely new jinja_loader
            this_app.jinja_loader = jinja2.ChoiceLoader([
                    jinja2.FileSystemLoader(host_template_dirs),
                    jinja2.FileSystemLoader(template_dirs),
                    jinja2.FileSystemLoader([this_app.template_folder,]),
            ])
            
            # ## this debug code will cause the session cookie to become to big
#             ##. and lead to unpredictable results
#             mes = []
#             for i in this_app.jinja_loader.loaders:
#                 try:
#                     mes.append(i.searchpath)
#                 except AttributeError:
#                     try:
#                         for j in i.loaders:
#                             try:
#                                 mes.append(j.searchpath)
#                             except AttributeError:
#                                 mes.append(str(j))
#                     except:
#                         pass
#
#             flash(mes)
            
            
        else:
            flash("app config 'TEMPLATE_DIRS' must be a list.")
    
                
    return this_app.config

def make_db_path(filespec):
    # test the path, if not found, create it
    root_path = os.path.dirname(os.path.abspath(__name__))
    if not os.path.isfile(os.path.join(root_path,filespec)):
        # split it into directories and create them if needed
        path_list = filespec.split("/")
        current_path = root_path
        for d in range(len(path_list)-1):
            current_path = os.path.join(current_path,path_list[d])
            if not os.path.isdir(current_path):
                os.mkdir(current_path, mode=0o744)
        return True
    return False

    
def user_setup():
    if 'admin' not in g:
        g.admin = Admin(g.db)
        # Add items to the Admin menu
        # the order here determines the order of display in the menu
        
    # a header row must have the some permissions or higher than the items it heads
    g.admin.register(User,url_for('user.display'),display_name='User Admin',header_row=True,minimum_rank_required=500)
        
    g.admin.register(User,url_for('user.display'),display_name='Users',minimum_rank_required=500,roles=['admin',])
    g.admin.register(Role,url_for('role.display'),display_name='Roles',minimum_rank_required=1000)
    g.admin.register(Pref,url_for('pref.display'),display_name='Prefs',minimum_rank_required=1000)
        

#
# @app.errorhandler(404)
def page_not_found(error):
    from shotglass2.takeabeltof.utils import handle_request_error
    handle_request_error(error,request,404)
    g.title = "Page Not Found"
    return render_template('404.html'), 404
#
# @app.errorhandler(500)
def server_error(error):
    from shotglass2.takeabeltof.utils import handle_request_error
    handle_request_error(error,request,500)
    g.title = "Server Error"
    return render_template('500.html'), 500


#@app.route('/static/<path:filename>')
def static(filename):
    """This takes full responsibility for loading static content"""
    #import pdb;pdb.set_trace()
    app_config = get_app_config()
    local_path = []
    local_config = app_config.get('LOCAL_STATIC_DIRS')
    static_config = app_config.get('STATIC_DIRS')
    if local_config:
        if not isinstance(local_config,list):
            raise TypeError('LOCAL_STATIC_DIRS must be a list')
            
        local_path = local_config
    if static_config:
        #append STATIC_DIRS to LOCAL_STATIC_DIRS
        if not isinstance(static_config,list):
            raise TypeError('STATIC_DIRS must be a list')
        for folder in static_config:
            local_path.append(folder)
        
    return send_static_file(filename,path_list=local_path)


def register_www(app):
    """I did this because I thought I could modify the routes
    at startup by modifying the routes var returned from get_default_routes
    Turns out flask complains that the routes already exist.
    If you really want to make more extensive changes, just copy the www blueprint
    into a new project and have your way with it."""
    
    from shotglass2.www.views import home
    routes = home.get_default_routes()
    for key, value in routes.items():
        home.mod.add_url_rule(value[0],value[1],value[2],**value[3])
    app.register_blueprint(home.mod)

def register_users(app):
    from shotglass2.users.views import user, login, role, pref
    app.register_blueprint(user.mod)
    app.register_blueprint(login.mod)
    app.register_blueprint(role.mod)
    app.register_blueprint(pref.mod)

