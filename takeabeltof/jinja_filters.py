from shotglass2.takeabeltof.date_utils import date_to_string, getDatetimeFromString
from shotglass2.takeabeltof.utils import render_markdown_text
from jinja2 import Markup
from datetime import datetime

# some custom filters for templates
def iso_date_string(value):
    """YYYY-MM-DD"""
    format = '%Y-%m-%d'
    return date_to_string(value,format)
        
        
def short_date_string(value):
    """mm/dd/yy"""
    format='%m/%d/%y'
    return date_to_string(value,format)
    
def local_date_string(value):
    """3/1/19"""
    format='%-m/%-d/%y'
    return date_to_string(value,format)
    
    
def local_date_and_time_string(value):
    """3/1/19 6:33AM"""
    format='%-m/%-d/%y %-I:%M%p'
    return date_to_string(value,format)


def short_day_and_date_string(value):
    """Mon. 3/4/19"""
    format='%a. %-m/%-d/%y'
    return date_to_string(value,format)
    
def short_day_and_date_and_time_string(value):
    """Mon. 3/4/19 6:00PM"""
    format='%a. %-m/%-d/%y %-I:%M%p'
    return date_to_string(value,format)
    
    
def long_date_string(value):
    """March 3, 2019"""
    format='%B %-d, %Y'
    return date_to_string(value,format)
    
def abbr_date_string(value):
    """Mon. Mar. 4, 2019"""
    format='%a, %b. %-d, %Y'
    #No period after May
    if type(value) is str:
        # convert the string to a date first then back.
        temp_date = getDatetimeFromString(value)
        if temp_date and temp_date.month == 5:
            format='%a, %b %-d, %Y'
            value = temp_date
        
    return date_to_string(value,format)
    
def short_abbr_date_string(value):
    """Mar. 4"""
    format='%b. %-d'
    return date_to_string(value,format)

def local_time_string(value):
    """6:00AM"""
    return date_to_string(value,'local_time')

def two_decimal_string(value):
    try:
        if type(value) is str:
            value = value.strip()
        if value == None or value == '':
            value = '0'
        value = float(value)
        value = (str(value) + "00")
        pos = value.find(".")
        if pos > 0:
            value = value[:pos+3]
    except ValueError as e:
        pass
        
    return value
    
    
def weblink(data,safe=True,blank=True):
    """Render a hyperlink for the data provided. Data is assumed to be a web address
    Open in new window/tab by default.
    
    5/28/19 - trim the displayed url to end after the tld
    """
    if data:
        # Ensute that this is an absolute address
        data_parts = data.strip().partition('//')
        if data_parts[0][:4] != 'http':
            data = 'http://' + data.strip()
            
        link_text = data.strip().replace('http://','').replace("https://",'').strip("/").split('/')[0]
        data = """<a href="{}">{}</a>""".format(data.strip().lower(),link_text)
        if blank:
            data = data.replace(">",' target="_blank" >',1)
        if safe:
            return Markup(data) # consider "safe"
        return data
        
    return ''
    
    
def render_markdown(data):
    """Return the text as html """
    if data:
        return Markup(render_markdown_text(data))
        
    return ''
    
    
def register_jinja_filters(app):
    # register the filters
    app.jinja_env.filters['short_date_string'] = short_date_string
    app.jinja_env.filters['short_day_and_date_string'] = short_day_and_date_string
    app.jinja_env.filters['short_day_and_date_and_time_string'] = short_day_and_date_and_time_string 
    app.jinja_env.filters['short_day_and_date'] = short_day_and_date_string #depricated
    app.jinja_env.filters['abbr_date_string'] = abbr_date_string
    app.jinja_env.filters['short_abbr_date_string'] = short_abbr_date_string
    app.jinja_env.filters['long_date_string'] = long_date_string
    app.jinja_env.filters['two_decimal_string'] = two_decimal_string
    app.jinja_env.filters['iso_date_string'] = iso_date_string
    app.jinja_env.filters['local_time_string'] = local_time_string
    app.jinja_env.filters['local_date_string'] = local_date_string
    app.jinja_env.filters['local_date_and_time_string'] = local_date_and_time_string
    app.jinja_env.filters['money'] = two_decimal_string
    app.jinja_env.filters['weblink'] = weblink
    app.jinja_env.filters['render_markdown'] = render_markdown
