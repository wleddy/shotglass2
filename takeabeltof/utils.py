"""takeabeltof.utils
    Some utility functions
"""

from flask import g, render_template_string, flash, send_from_directory, abort
from shotglass2.takeabeltof.date_utils import nowString
import linecache
import sys
import re
import random
import mistune # for Markdown rendering
import os


def cleanRecordID(id):
    """ return the integer version of id or else -1 """
    if id is None:
        return -1
    if type(id) is str: # or type(id) is unicode:
        if id.isdigit():
            # a negative number like "-1" will fail this test, which is what we want
            return int(id)
        else:
            return -1
            
    #already a number 
    return id
    
def looksLikeEmailAddress(email=""):
    """Return True if str email looks like a normal email address else False"""
    if type(email) is not str:
        return False
        
    return re.match(r"[^@]+@[^@]+\.[^@]+", email.strip())
    
def printException(mes="An Unknown Error Occurred",level="error",err=None):
    from shotglass2.shotglass import get_app_config 
    from app import app
    
    app_config = get_app_config()
    
    exc_type, exc_obj, tb = sys.exc_info()
    debugMes = None
    if tb is not None:
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        try:
            debugMes = 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
        except ValueError:
            debugMes = "Could not get error location info."
            
    if level=="error" or app_config["DEBUG"]:
        #always log errors
        if debugMes:
            app.logger.error(nowString() + " - " + debugMes)
        app.logger.error(nowString() + "   " + mes)
        if err:
            app.logger.error(nowString() + "    " + str(err))
        
    if app_config["DEBUG"]:
        if debugMes:
            mes = mes + " -- " +debugMes
        return mes
    else:
        return mes
        
        
def render_markdown_for(file_name,bp=None,**kwargs):
    """Try to find the file to render and then do so
    if file_name has a leading slash, it will be treated as an apbolute path
    by os.path.join. If that's not what you were expecting, you need to
    remove any leading slashes before calling this function.
    
    (In particular, the shotglass.home.docs route depends on this fact.)
    
    """
    from shotglass2.shotglass import get_app_config
    #import pdb;pdb.set_trace()
    
    app_config = get_app_config()
    
    def valid_file_path(file_path):
        """Test the file path and return true if exists, else false
        if explain is True, print a report
        """
        explain = app_config.get('EXPLAIN_TEMPLATE_LOADING',False)
        
        if os.path.isfile(file_path):
            if explain:
                print('found: {}'.format(file_path))
            return True
        else:
            if explain:
                print('not found: {}'.format(file_path))
            return False
            
    
    rendered_html = None
    markdown_path = ''
        
    if type(file_name) != str:
        file_name = ''
            
    application_path = os.path.dirname(os.path.abspath(__name__))
    
    # search the directories in the same way flask does
    for directory in g.template_list:
        markdown_path = os.path.join(application_path,directory,file_name)
        if valid_file_path(markdown_path):
            break

    if not valid_file_path(markdown_path):
        # next, try docs
        markdown_path = os.path.join(application_path, 'docs',file_name)
    if not valid_file_path(markdown_path) and bp:
        # look in the templates directory of the calling blueprint
        bp_template_folder = 'templates' #default
        if bp.template_folder:
            bp_template_folder = bp.template_folder
        
        markdown_path = os.path.join(application_path,bp_template_folder,file_name)
        if not valid_file_path(markdown_path):
            # look in the template folder of the blueprint
            markdown_path = os.path.join(bp.root_path, bp_template_folder,file_name)
    if valid_file_path(markdown_path):
        f = open(markdown_path)
        rendered_html = f.read()
        f.close()
                
        rendered_html = render_markdown_text(rendered_html,**kwargs)
    elif app_config['DEBUG']:
        ### TESTING Note: the test is looking for the text 'no file found' in this return.
        source_script = ''
        if bp:
            source_script = ' called from {}'.format(bp.import_name)
        rendered_html = "Because you're in DEBUG mode, you should know that there was no file found: '{}'{}".format(file_name,source_script,)

    return rendered_html


def render_markdown_text(text_to_render,**kwargs):
    # treat the markdown as a template and render url_for and app.config values
    text_to_render = render_template_string(text_to_render,**kwargs)
    escape = kwargs.get('escape',True) #Set to False to preserve included html
    markdown = mistune.Markdown(renderer=mistune.Renderer(escape=escape))
    return markdown(text_to_render)
    
    
def handle_request_error(error=None,request=None,status=666):
    """Usually used to handle a basic request error such as a db error"""
    from shotglass2.takeabeltof.mailer import alert_admin
    from shotglass2.shotglass import get_app_config
    app_config = get_app_config()
    
    error_mes = 'The following error was reported from {}. \nRequest status: {}\n\n'.format(app_config['SITE_NAME'],status)
    if not error:
        error_mes += "Error message not provided"
    else:
        error_mes += str(error)
        
    if request:
        error_mes += '\n\nRequest URL: {}'.format(request.url)
        
    printException(error_mes)
    
    try:
        if (status == 404 and app_config['REPORT_404_ERRORS']) or status != 404:
            alert_admin("Request error [{}] at {}".format(status,app_config['HOST_NAME']),error_mes)
    except Exception as e:
        flash(printException("An error was encountered in handle_request_error. {}".format(str(e))))
        
    return error_mes # just to make it testable
        
        
def send_static_file(filename,**kwargs):
    """Send the file if it exists, else try to send it from the static directory"""
    
    path_list = kwargs.get('path_list',['static','shotglass2/static'])
    
    path = None
    
    for temp_path in path_list:
        file_loc = os.path.join(os.path.dirname(os.path.abspath(__name__)),temp_path,filename)
        if os.path.isfile(file_loc):
            path = temp_path
            break
    
    if path:
        return send_from_directory(path,filename, as_attachment=False)
            
    return abort(404)
    
    