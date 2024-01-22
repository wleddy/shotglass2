from flask import Flask, render_template, g, url_for, request, flash
import logging
from logging.handlers import RotatingFileHandler
from shotglass2.takeabeltof.sqlite_backup import SqliteBackup
from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.takeabeltof.utils import send_static_file
from shotglass2.users.models import User,Role,Pref
from shotglass2.users.admin import Admin
import os  
import threading
import time
  
  
def create_app(name,instance_path=None,config_filename=None,**kwargs):
    """Initialize and return an instance of the flask app
    
    Args:
        name; string, the name of the app. Usually __name__
        instance_path: string, a path to the instance directory
        config_filename: string, name of the config file
        kwargs: optional keyword settings
        
    """
    
    # setting static_folder to None allows me to handle loading myself
    
    instance_path = instance_path or 'instance'
    config_filename = config_filename or 'settings.py'
    
    static_folder=kwargs.get('static_folder','static')
    template_folder=kwargs.get('template_folder','templates')
    
    app = Flask(name,static_folder=static_folder,template_folder=template_folder)
    
    app.instance_relative_config=True
    app.instance_path = os.path.normpath(os.path.join(app.root_path,instance_path))
    app.config.from_pyfile(os.path.join(app.instance_path,config_filename))
    
    return app
    

def get_menu_items():
    """The default items for the navigation menu
    
    So that you can add items to the menu without modifying
    shotglass2/templates/top-nav.html. 
    
    To modify, copy this list to app.py @before_request function.
    
    For a drop down menu, use something like this:
    
    `{'title':'Home','drop_down_menu':[
        {'title':'Events Home','url':url_for('www.home')},
        {'title':'SABA Home','url':'http://sacbike.org'},
        ]
      },`
    
    """
    menu_items = [
        {'title':'Home','url':url_for('www.home')},
        {'title':'About','url':url_for('www.about')},
        {'title':'Contact Us','url':url_for('www.contact')},
        {'title':'Docs','url':url_for('www.docs')},
        ]
    return menu_items
    
    
def get_site_config(this_app=None):
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

    ## Changing the contents of app.config after startup is a bad idea, so work on a copy instead
    ### This implys that any place you want to get the current site specific config you must use site_config instead of app.config
    site_config = this_app.config.copy()

    if request_in_flight and "SHARED_HOST_SETTINGS" in site_config and len(site_config["SHARED_HOST_SETTINGS"]) > 0:
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
                site_config[key.upper()] = value

        except:
            # Will use the default settings
            if site_config['DEBUG']:
                #raise ValueError("SHARED_HOST_SETTINGS could not be determined")
                flash("Using Default SHARED_HOST_SETTINGS")
    
    return site_config


def initalize_user_tables(db):
    """Initialize the Users, Prefs and Roles tables"""
            
    from shotglass2.users.models import init_db as users_init_db 
    users_init_db(db)
    
    
def is_ajax_request():
    """Return True if this request was submitted as XMLHttpRequest else False"""
    try:
        return request.headers.get('X-Requested-With') ==  'XMLHttpRequest'
    except AttributeError:
        #there is no request?
        pass
        
    return False
    
def make_db_path(filespec):
    # to support old code...
    return make_path(filespec)
    
    
def make_path(filespec):
    """
    Test the filespec path and if not found, create the path
    but not the file if a file name is included in the path.
    Returns True if either the path already existed or was
    created.
    
    If filespec is an absolute path, use as is. If not, use
    app.root_path (the path to the application file) instead.
    """
    
    if os.path.isabs(filespec):
        root_path = os.path.dirname(filespec)
    else:
        # if filespec is not an absolute path, use app.root_path as the starting point
        from app import app
        root_path = os.path.join(app.root_path,os.path.dirname(filespec))
        
    if not os.path.isdir(root_path) :
        # split it into directories and create them if needed
        path_list = root_path.split("/")
        current_path = '/'
        try:
            for d in path_list:
                current_path = os.path.join(current_path,d)
                if not os.path.isdir(current_path):
                    os.mkdir(current_path, mode=0o744)
            return True
        except Exception as e:
            return False
    return True


def register_users(app,subdomain=None):
    mes = 'shotglass.register_users should be replaced with users.register_users'
    from app import app
    app.logger.warning(mes)

    from shotglass2.users.views import user, login, role, pref
    app.register_blueprint(user.mod, subdomain=subdomain)
    app.register_blueprint(login.mod, subdomain=subdomain)
    app.register_blueprint(role.mod, subdomain=subdomain)
    app.register_blueprint(pref.mod, subdomain=subdomain)


def register_www(app,subdomain=None):
    from shotglass2.www.views import home
    app.register_blueprint(home.mod, subdomain=subdomain)


def register_maps(app,subdomain=None):
    from shotglass2.mapping.views import maps
    app.register_blueprint(maps.mod,subdomain=subdomain)
    
    
def page_not_found(error):
    from shotglass2.takeabeltof.utils import handle_request_error
    handle_request_error(error,request)
    g.title = "Page Not Found"
    return render_template('404.html'), 404


def server_error(error):
    from shotglass2.takeabeltof.utils import handle_request_error
    handle_request_error(error,request)
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

    
def static(filename):
    """This takes full responsibility for loading static content"""
    #import pdb;pdb.set_trace()
    from app import app
    site_config = get_site_config()
    local_path = []
    local_config = site_config.get('LOCAL_STATIC_DIRS')
    static_config = site_config.get('STATIC_DIRS')
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
    # To support old app.py code
    set_user_menus()


def set_user_menus():
    if 'admin' not in g:
        g.admin = Admin(g.db)
        # Add items to the Admin menu
        # the order here determines the order of display in the menu
        
    # a header row must have the some permissions or higher than the items it heads
    g.admin.register(User,url_for('user.display'),display_name='User Admin',header_row=True,minimum_rank_required=500)
        
    g.admin.register(User,url_for('user.display'),display_name='Users',minimum_rank_required=500,roles=['admin',])
    g.admin.register(Role,url_for('role.display'),display_name='Roles',minimum_rank_required=500)
    g.admin.register(Pref,url_for('pref.display'),display_name='Prefs',minimum_rank_required=500)
        
        
class ShotLog():
    """Handle creation and access to log"""
    
    def __init__(self,log_file_path=None,level=logging.INFO):
        site_config = get_site_config()
        self.log_file_path = log_file_path or site_config.get('INSTANCE_PATH','instance/') + site_config.get('LOG_FILE_NAME',"log.log")
        self.log_level = level

    def start(self,app,filename=None,maxBytes=10000,backupCount=5):
        filename = filename if filename else self.log_file_path
    
        # initialize the log handler
        logHandler = RotatingFileHandler(filename=filename, maxBytes=maxBytes, backupCount=backupCount)


        # set the log handler level
        logHandler.setLevel(self.log_level)
        # set the app logger level
        app.logger.setLevel(self.log_level)

        app.logger.addHandler(logHandler)
        
        
    def get_text(self):
        # return the contents of the log in reverse order mostly for display

        # def reverse_readline(filename, ):
        """A generator that returns the lines of a file in reverse order"""
        with open(self.log_file_path) as fh:
            buf_size=8192
            segment = None
            offset = 0
            fh.seek(0, os.SEEK_END)
            file_size = remaining_size = fh.tell()
            while remaining_size > 0:
                offset = min(file_size, offset + buf_size)
                fh.seek(file_size - offset)
                buffer = fh.read(min(remaining_size, buf_size))
                remaining_size -= buf_size
                lines = buffer.split('\n')
                # The first line of the buffer is probably not a complete line so
                # we'll save it and append it to the last line of the next buffer
                # we read
                if segment is not None:
                    # If the previous chunk starts right from the beginning of line
                    # do not concat the segment to the last line of new chunk.
                    # Instead, yield the segment first 
                    if buffer[-1] != '\n':
                        lines[-1] += segment
                    else:
                        yield segment
                segment = lines[0]
                for index in range(len(lines) - 1, 0, -1):
                    if lines[index]:
                        yield lines[index]
            # Don't yield None if the file was empty
            if segment is not None:
                yield segment
 
    
def start_logging(app,filename=None,maxBytes=100000,backupCount=5,level=logging.INFO):
    # to handle legacy code
    log = ShotLog(level=level)
    log.start(app,filename=None,maxBytes=100000,backupCount=5)
    
    
def do_backups(source_file_path,**kwargs):
    """
    Make a series of backups of the sqlite3 database file
    
    **params**:
    
    * **source_file_path**: The path to database file to backup
    
    **kwargs**:
    
    * **exit_after**: An integer to limit howmay times the loop will run.
    It does not mean that there will be that many backups made. Just that
    many tries. If exit_after is less than 0, run forever.
    
    * The remainting kwargs are passed to the SqliteBackup constructor
    
    """
    from app import app
    from shotglass2.takeabeltof.mailer import email_admin
    
    exit_after = int(kwargs.pop('exit_after',-1))
    
    bac = SqliteBackup(source_file_path,**kwargs)
    time.sleep(2)
    
    loop_counter = 0

    while not bac.fatal_error and (exit_after < loop_counter):
        loop_counter += 1
        bac.backup()
        
        if app.config['TESTING']:
            return bac
            
        if bac.fatal_error:
            mes = "[{}] -- Backup error : {}, code: {}".format(local_datetime_now(),bac.result,bac.result_code)
            # log the error
            app.logger.error(mes)
            # send for the calvery
            email_admin("Fatal Backup Error Occurred",mes)
            break
        else:
            # limit the amount of logging the backup process does
            if app.config['DEBUG'] or bac.result_code == 0 or bac.result_code >= 10:
                app.logger.info("[{}] -- Backup Result: {}, code: {}".format(local_datetime_now(),bac.result,bac.result_code))

            time.sleep(30*60) #sleep for half an hour
    
    
def start_backup_thread(source_file_path,**kwargs):
    """
    Create a thread to run do_backups in
    """
    from app import app
    
    # set daemon to True so the thread will terminate when the originating thread (app) teminates
    backup_thread = threading.Thread(target=do_backups,args=(source_file_path,),kwargs=kwargs,name='backup_thread',daemon=True)

    backup_thread.start()
    if app.config['DEBUG']:
        app.logger.info("[{}] -- Backups started in a new thread".format(local_datetime_now()))
    