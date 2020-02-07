"""takeabeltof.utils
    Some utility functions
"""

from flask import g, render_template_string, flash, send_from_directory, abort, url_for
from shotglass2.takeabeltof.date_utils import nowString
import linecache
import sys
import re
import random
import mistune # for Markdown rendering
import os


def cleanRecordID(id):
    """ return the integer version of id or else -1 """
    if type(id) is str: # or type(id) is unicode:
        if id.isdigit():
            # a negative number like "-1" will fail this test, which is what we want
            return int(id)
        else:
            pass
            
    if isinstance(id,(int,float)):
        #already a number 
        return int(id)
        
    return -1
    
def looksLikeEmailAddress(email=""):
    """Return True if str email looks like a normal email address else False"""
    if type(email) is not str:
        return False
        
    return re.match(r"[^@]+@[^@]+\.[^@]+", email.strip())
    
def printException(mes="An Unknown Error Occurred",level="error",err=None):
    """Generate an error message, write it to the log and return the resulting
    text.
    
    mes: Some message text specific to the supposed cause of the error.
    
    level: Any of 'error', 'info', 'debug'
    
    When logging or in debug mode attempts to generate a description of the error
    location.
    
    """
    from shotglass2.shotglass import get_site_config 
    from app import app
    
    site_config = get_site_config()
    level = level.lower()
    
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
            
    if level=="error" or site_config["DEBUG"]:
        if debugMes:
            app.logger.error(nowString() + " - " + debugMes)
        elif err:
            app.logger.error(nowString() + " - Error: " + str(err))
            
    if mes:
        app.logger.error(nowString() + " - " + mes)
        
    if site_config["DEBUG"]:
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
    from shotglass2.shotglass import get_site_config
    #import pdb;pdb.set_trace()
    
    site_config = get_site_config()
    
    def valid_file_path(file_path):
        """Test the file path and return true if exists, else false
        if explain is True, print a report
        """
        explain = site_config.get('EXPLAIN_TEMPLATE_LOADING',False)
        
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
                
        # - 12/3/2019 - Initial attempt to handle Sphynx documentaion
        """
        Sphynx renders complete HTML documents so, in reality we don't want to modify them
        except, that we want pull the contents out of <body> and throw away everything else
        
        Look for "documentation_options" in the text which is something Sphynx puts in the <head> section
        """
        if "documentation_options" in rendered_html:
            x = rendered_html.find('<body>')
            y = rendered_html.find('</body')
            if x >= 0 and y > 0:
                rendered_html = rendered_html[x+6:y]
                # fix the relative references for images etc.
                rendered_html = rendered_html.replace('src="../','src="/static/')
                # fix hrefs too for images...
                rendered_html = rendered_html.replace('href="../_images','href="/static/_images')
        else:
            rendered_html = render_markdown_text(rendered_html,**kwargs)
            
    elif site_config['DEBUG']:
        ### TESTING Note: the test is looking for the text 'no file found' in this return.
        source_script = ''
        if bp:
            source_script = ' called from {}'.format(bp.import_name)
        rendered_html = "Because you're in DEBUG mode, you should know that there was no file found: '{}'{}".format(file_name,source_script,)

    return rendered_html


def render_markdown_text(text_to_render,**kwargs):
    """Convert text_to_render to html
    
    Renders the markdown as a template first so that any included Jinja template values
    will be rendered to text before markdown conversion to html.
    
    __kwargs__ can contain anything that you want to use in the template context.
    
    The following kwargs may also be present:
        escape: Default to True. If false any included html in the text will be left as-is
        and not escaped for display
    
    """ 
    text_to_render = render_template_string(text_to_render,**kwargs)
    escape = kwargs.get('escape',True) #Set to False to preserve included html
    markdown = mistune.Markdown(renderer=mistune.Renderer(escape=escape))
    return markdown(text_to_render)
    
    
def handle_request_error(error=None,request=None):
    """Usually used to handle a basic request error such as a db error"""
    from shotglass2.takeabeltof.mailer import alert_admin
    from shotglass2.shotglass import get_site_config
    site_config = get_site_config()
    #import pdb; pdb.set_trace()
    mes = "An unknown error occured"
    level = "error"
    request_url = "No URL supplied"
    if request and hasattr(request,'url'):
        request_url = request.url
        
    try:
        if error:
            if hasattr(error,'code'):
                mes = 'The following error was reported from {}. Request status: {} '.format(site_config['SITE_NAME'],error.code)
                if request:
                    mes += ' - Request URL: {}'.format(request_url)
        
                level = 'info' if error.code == 404 else "error"
                if (error.code == 404 and site_config['REPORT_404_ERRORS']) or error.code != 404:
                    if request and 'apple-touch-icon' not in request_url and 'favicon' not in request_url:
                        alert_admin("Request error [{}] at {}".format(error.code,site_config['HOST_NAME']),mes)
                        printException(mes,level=level,err=error)
            else:
                temp_mes = str(error)
                mes = printException("The following error occured: {} during request for {}".format(temp_mes,request_url),level=level,err=error)
                alert_admin("System error from {}".format(site_config['SITE_NAME']),mes)
        else:
            mes = "Error message not provided"
        
    
    except Exception as e:
        alert_admin(printException("An error was encountered in handle_request_error.",err=e))
        
    return mes # just to make it testable
        
        
def send_static_file(filename,**kwargs):
    """Send the file if it exists, else try to send it from the static directory"""
    from shotglass2.shotglass import get_site_config
    
    path_list = kwargs.get('path_list',['static','shotglass2/static'])
    
    path = None
    
    explain = get_site_config().get('EXPLAIN_TEMPLATE_LOADING',False)
    
    if explain:
        print("\nSearching for {}".format(filename))
    
    for temp_path in path_list:
        file_loc = os.path.join(os.path.dirname(os.path.abspath(__name__)),temp_path,filename)
        if os.path.isfile(file_loc):
            path = temp_path
            if explain:
                print("{} was found at {}".format(filename,os.path.join(os.path.dirname(os.path.abspath(__name__)),temp_path)))
            break
        else:
            if explain:
                print("{} was not found at {}".format(filename,os.path.join(os.path.dirname(os.path.abspath(__name__)),temp_path)))
    
    if path:
        return send_from_directory(path,filename, as_attachment=False)
            
    return abort(404)
    
    
def formatted_phone_number(phone,sep="-",raw=False):
    """Take what may be a phone number and return a formatted version of it.
    
    params:
        phone: a string that may be a phone number
        
        sep: the string value to use as a separator in the converted string
        
        raw: if True the function returns a tuple of found parts
    
    If the value can't be converted, the value is returned unchanged.
    
    Taken from: https://www.diveinto.org/python3/regular-expressions.html
    """
    
    if type(phone) != str:
        return phone
        
    phonePattern = re.compile(r'(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$')
    try:
        groups = phonePattern.search(phone).groups()
    except AttributeError:
        # No match found
        return phone
        
    if groups:
        if raw:
            return groups
            
        if len(groups) > 2:
             return sep.join(groups[:3])
             
    return phone # conversion failed
    