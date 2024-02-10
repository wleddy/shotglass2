from shotglass2.takeabeltof.date_utils import date_to_string, getDatetimeFromString
from shotglass2.takeabeltof.utils import render_markdown_text, formatted_phone_number
from markupsafe import Markup
from datetime import datetime
import re

# some custom filters for templates
def iso_date_string(value):
    """YYYY-MM-DD"""
    format = '%Y-%m-%d'
    return date_to_string(value,format)

def more(value,size=80,more_text="More...") ->str:
    """
    return value with a couple <span>s that will allow
    it to be styled to trunkate value but dislay when clicked

    Arguments:
        value -- a string

    Keyword Arguments:
        size -- How many characters to always display (default: {80})
        more_text -- Text to put in the middle span (default: {"More..."})

    Returns:
        a string
    """

    if len(value) <= size:
        return value # too short
    
    first = value[:size-1]
    # find a trailing space in first
    while first[-1] not in [" ","/n"] and len(first) > size - 10:
        size -= 1
        # resize first
        first = value[:size-1]
    tail = value[size-1:]

    return f'{first}<span>{more_text}</span><span>{ tail }</span>'


def sanitize(value) ->str:
    """
    Attempt to remove any dangerous content from "safe" text.
    BE SURE TO CALL THIS BEFORE "safe" filter

    Arguments:
        value -- a string

    Returns:
        a string
    """

    forbidden = [
        "<script",
        "</script>",
        "<a",
        "</a>",
    ]

    for baddy in forbidden:
        value = value.replace(baddy,"")

    return value
        
   
def short_date_string(value):
    """mm/dd/yy"""
    format='%m/%d/%y'
    return date_to_string(value,format)
    
def local_date_string(value):
    """3/1/19"""
    format='%-m/%-d/%y'
    return date_to_string(value,format)
    
    
def local_date_and_time_string(value):
    """Return a datetime as short date and AM/PM time. Ex: '3/1/19 6:33AM'"""
    format='%-m/%-d/%y %-I:%M%p'
    return date_to_string(value,format)

def excel_date_and_time_string(value):
    """Return a datetime as short date and AM/PM time with an extra space. 
    Ex: '3/1/19 6:33 AM'
    
    Excel does not seem to be able to recognize as a datetime without the space 
    before AM/PM
    """
    format='%-m/%-d/%y %-I:%M %p'
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
    format='%a. %b. %-d, %Y'
        
    if type(value) is str:
        # convert the string to a date first then back.
        value = getDatetimeFromString(value)
        
    #No period after May
    if value.month == 5:
        format='%a. %b %-d, %Y'
        
    return date_to_string(value,format)
    
def short_abbr_date_string(value):
    """Mar. 4"""
    format='%b. %-d'
    return date_to_string(value,format)

def local_time_string(value):
    """6:00AM"""
    return date_to_string(value,'local_time')

def two_decimal_string(value,denomination=''):
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

        if denomination:
            value = denomination + value
    except ValueError as e:
        pass
        
    return value
    
    
def phone(value,sep='-',raw=False):
    """Return a formatted phone number"""
    return formatted_phone_number(value,sep,raw)
        
    
def weblink(data,safe=True,blank=True):
    """Render a hyperlink for the data provided. Data is assumed to be a web address
    Open in new window/tab by default.
    
    :note: 5/28/19 - trim the displayed url to end after the tld
    """
    out = ''
    
    if data:
        # Ensute that this is an absolute address
        parts = data.partition("//")
        data_part = [x.strip() for x in parts] #convert to a list to make it simplier
            
        if data_part[0] != '' and data_part[2] == '':
            # no // present. host name at [0]
            data_part[2] = data_part[0]
            data = 'http://' + data_part[2]
        
        if data_part[2].strip() == '':
            # there is no host name part
            data = ''
            
        elif data_part[0][:4] != 'http':
            data = 'http://' + data_part[2]
            
        # data should now look like a valid url
        if data and re.match(r'(http|https)://.*?\.\S\S\S?',data):
            link_text = data.replace('http://','').replace("https://",'').strip("/").split('/')[0]
            out = """<a href="{}">{}</a>""".format(data.lower(),link_text)
            if blank:
                out = out.replace(">",' target="_blank" >',1)
            if safe:
                out = Markup(out) # consider "safe"
        
    return out
    
    
def render_markdown(data):
    """Return the text as html """
    if data:
        return Markup(render_markdown_text(data))
        
    return ''
    
    
def default_if_none(data,value='',default_on_false=False):
    """Return the default value if data is None
    
    Optionally, if default_on_false is True, return the default value
    if data evaluates as False.
    
    """
    if data == None or (not data and default_on_false):
        return value
        
    return data
    
    
def plural(value,count=2,plural_form=None):
    """Return the value <str> as a string
    
    if plural_form is provided, return that if count != 1
    """

    irregulars = {
        'aircraft': 'aircraft',
        'alumna': 'alumnae',
        'analysis': 'analyses',
        'apex': 'apices',
        'appendix': 'appendices',
        'bison': 'bison',
        'cactus': 'cacti',
        'child': 'children',
        'codex': 'codies',
        'crisis': 'crises',
        'curriculum': 'curricula',
        'datum': 'data',
        'die': 'dice',
        'diagnosis': 'diagnoses',
        'ellipsis': 'ellipses',
        'erratum': 'errata',
        'fish': 'fishes',
        'focus': 'foci',
        'foot': 'feet',
        'genus': 'genera',
        'goose': 'geese',
        'index': 'indices',
        'larva': 'larvae',
        'leaf': 'leaves',
        'louse': 'lice',
        'man': 'men',
        'mouse': 'mice',
        'oasis': 'oases',
        'ox': 'oxen',
        'person': 'people',
        'quiz': 'quizzes',
        'series': 'series',
        'sheep': 'sheep',
        'swine': 'swine',
        'tooth': 'teeth',
        'trout': 'trout',
        'tuna': 'tuna',
        'vita': 'vitae',
        'woman': 'women',
    }

    if not isinstance(value,str):
        return value

    if isinstance(count,str):
        try:
            count = int(count)
        except:
            return value
    # test if count is some kind of iterable
    try:
        count = len(count)
    except:
        pass
        
    if count == 1:
        # not a plural
        return value
    
    if plural_form and count != 1:
        return plural_form
    
    plural =  irregulars.get(value.lower())
    if plural:
        pass
    elif value[-1].lower() == 'y':
        plural =  value[:-1] + 'ies'
    elif value[-1].lower() == 'f':
        # 'wolf' => 'wolves'
        plural =  value[:-1] + 'ves'
    elif value[-1].lower() == 's':
        plural =  value + 'es'
    else:
        plural = value + 's'
        
    # set the capitalization to match if we can
    if value.isupper():
        plural = plural.upper()
    elif value.istitle():
        plural = plural.title()
        
    return plural
    
    
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
    app.jinja_env.filters['excel_date_and_time_string'] = excel_date_and_time_string
    app.jinja_env.filters['money'] = two_decimal_string
    app.jinja_env.filters['weblink'] = weblink
    app.jinja_env.filters['render_markdown'] = render_markdown
    app.jinja_env.filters['default_if_none'] = default_if_none
    app.jinja_env.filters['plural'] = plural
    app.jinja_env.filters['phone'] = phone
    app.jinja_env.filters['more'] = more
    app.jinja_env.filters['sanitize'] = sanitize
