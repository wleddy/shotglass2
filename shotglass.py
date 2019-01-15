from flask import render_template, g, url_for, request, flash
from flask_mail import Mail
from shotglass2.takeabeltof.utils import send_static_file
from shotglass2.users.models import User,Role,Pref
from shotglass2.users.admin import Admin
import os    


def get_app_config(this_app=None):
    """Returns a copy of the current app.config.
    This makes it possible for other modules to get access to the config
    with the values as updated for the current host.
    Import this method rather than importing app

    When called from app.py, the app is passed in. When
    called from other modules it is not needed.
    """   
    
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

    if request_in_flight and "SHARED_HOST_SETTINGS" in this_app.config and len(this_app.config["SHARED_HOST_SETTINGS"]) > 0:
        try:
            server = None
            for value in this_app.config['SHARED_HOST_SETTINGS']:
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
                #raise ValueError("SHARED_HOST_SETTINGS could not be determined")
             flash("Using Default SHARED_HOST_SETTINGS")
    
    return this_app.config


def initalize_user_tables(db):
    """Initialize the Users, Prefs and Roles tables"""
        
    from shotglass2.users.models import init_db as users_init_db 
    users_init_db(db)
    
        
def make_db_path(filespec):
    """Test the filespec path and if not found, create the path
    but not the file.
    Returns True if a new path was created, else False
    """
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


# @app.errorhandler(404)
def page_not_found(error):
    from shotglass2.takeabeltof.utils import handle_request_error
    handle_request_error(error,request,404)
    g.title = "Page Not Found"
    return render_template('404.html'), 404


def register_users(app):
    from shotglass2.users.views import user, login, role, pref
    app.register_blueprint(user.mod)
    app.register_blueprint(login.mod)
    app.register_blueprint(role.mod)
    app.register_blueprint(pref.mod)


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


# @app.errorhandler(500)
def server_error(error):
    from shotglass2.takeabeltof.utils import handle_request_error
    handle_request_error(error,request,500)
    g.title = "Server Error"
    return render_template('500.html'), 500


def set_template_dirs(this_app):
    """Compile a list of potential paths to search for
    template files.
    
    sets the global g.template_list with the search paths and
    sets app.jinja_loader which flask will use when searching
    
    Neither g.template_list nor app.jinja_loader will contain paths
    to the blueprint template directories. Flask handles that after
    the initial search so this works the same way.
    """
    
    #update the jinja loader
    import jinja2
    template_dirs = this_app.config.get('TEMPLATE_DIRS',['templates'])
    host_template_dirs = this_app.config.get('HOST_TEMPLATE_DIRS',[])
    if template_dirs:
        if isinstance(template_dirs,list):
            host_dir = host_template_dirs.copy()
            host_template_dirs = [] #start fresh
            if host_dir:
                if isinstance(host_dir,list):
                    for j in range(len(host_dir)):
                        host_template_dirs.append(host_dir[j])
                        for i in range(len(template_dirs)):
                            host_template_dirs.append(os.path.join(host_dir[j],template_dirs[i]))
                else:
                    flash("app config 'HOST_TEMPLATE_DIRS' must be a list.")
        else:
            flash("app config 'TEMPLATE_DIRS' must be a list.")
    
    #Save it for later render_markdown_for wants to use it
    #import pdb;pdb.set_trace()
    g.template_list = []
    g.template_list.extend(host_template_dirs)
    g.template_list.extend(template_dirs)
    g.template_list.extend([this_app.template_folder,'shotglass2/templates'])
    
    # generate a completely new jinja_loader
    this_app.jinja_loader = jinja2.ChoiceLoader([
            jinja2.FileSystemLoader(g.template_list),
    ])

    
#@app.route('/static/<path:filename>')
def static(filename):
    """This takes full responsibility for loading static content"""
    #import pdb;pdb.set_trace()
    from app import app
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
        local_path.extend(static_config)
        
    #Add relative static_folder from app blueprints
    for key, value in app.blueprints.items():
        if value._static_folder:
            local_path.append(value._static_folder)
    #Add absolute static_folder from app blueprints
    for key, value in app.blueprints.items():
        if value.static_folder:
            local_path.append(value.static_folder)
                
    # Finally add the default search paths
    local_path.extend(['static','shotglass2/static'])

    return send_static_file(filename,path_list=local_path)


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
        

