"""Some date utilities"""

from datetime import datetime, timedelta, date
from pytz import timezone

def local_datetime_now(time_zone=None):
    """Return a datetime object for now at the time zone specified.
    
    If tz is None, use the tz name in app.config else use the local time per the server"""
    if time_zone == None:
        time_zone = get_time_zone_setting()
        if time_zone == None:
            return datetime.now()
        
    try:
        #import pdb;pdb.set_trace()
        utc = timezone("UTC")
        local_tz = timezone(time_zone)
        now = utc.localize(datetime.utcnow())
        return now.astimezone(local_tz)
        
    except:
        return datetime.now()
            
def make_tz_aware(the_datetime,time_zone=None):
    """Return the time zone aware version of the datetime 
    This function will not convert an aware datetime to a new time zone"""
    if the_datetime.tzinfo != None:
        return the_datetime # not needed
        
    if time_zone == None:
        time_zone = get_time_zone_setting()
        if time_zone == None:
            time_zone = 'UTC'
            
    tz = timezone(time_zone)
    return tz.localize(the_datetime)
    
    
def get_time_zone_setting():
    """Return the TIME_ZONE config setting if it exists else None"""
    try:
        from shotglass2.shotglass import get_site_config
        
        time_zone = get_site_config()['TIME_ZONE']
    except:
        time_zone = None
        
    return time_zone
    
    
def nowString():
    """Return the timestamp string in the normal format"""
    return datetime_as_string(local_datetime_now())
    
    
def date_to_string(value,format):
    """Attempt to return a date string in the format specified
    value may be a datetime or a 'date like' string"""
    
    formats ={
    'date':"%m/%d/%y",
    'date_full_year': "%m/%d/%Y",
    'datetime-local' : '%Y-%m-%dT%H:%M',
    'time':'%I:%M',
    'time_long':'%H:%M:%S',
    'ampm': '%p',
    'local_time': '%-I:%M%p',
    'iso_date': '%Y-%m-%d',
    'iso_datetime': '%Y-%m-%d %H:%M:%S',
    'iso_8601': '%Y-%m-%dT%H:%M:%S',
    'iso_date_tz': '%Y-%m-%d %H:%M:%S%z',
    }
    
    #try to find the format in the dict
    format = formats.get(format,format)
        
    if value and format:
        if isinstance(value,(date,datetime)):
            return value.strftime(format)
        if isinstance(value,str):
            # convert the string to a date first then back.
            temp_date = getDatetimeFromString(value)
            if temp_date:
                return temp_date.strftime(format)
    
    #default - return unchanged
    return value

    
def datetime_as_string(the_datetime=None):
    """Return a string version of the datetime provided or for now"""
    if the_datetime == None:
        the_datetime = local_datetime_now()
        
    return the_datetime.isoformat(sep=" ")[:19]
    

def getDatetimeFromString(dateString):
    """Try to create a datetime object based on the string provided
    or else None.
    The  datetime object returned is time zone aware
    """
    if type(dateString) is str: # or type(dateString) is unicode:
        pass
    elif isinstance(dateString,(date,datetime)):
        #already a datetime. just make sure it's timezone aware
        if type(dateString) is date:
            # date object must be converted to datetime to be time zone aware
            dateString = datetime(dateString.year,dateString.month,dateString.day,0,0,0)
        if not dateString.tzinfo:
            dateString = timezone(get_time_zone_setting()).localize(dateString)
        return dateString
    else:
        return None

    dateString = dateString.strip()[:19]
    timeDelimiter = " "
    if "T" in dateString:
        timeDelimiter = "T"

    formats = [
        '%m/%d/%y',
        '%m/%d/%Y',
        '%m-%d-%y',
        '%m-%d-%Y',
        '%y-%m-%d',
        '%Y-%m-%d',
        '%y/%m/%d',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d/%m/%y',
        '%d-%m-%Y',
        '%d-%m-%y',
        '%m/%d/%y{}%H:%M:%S'.format(timeDelimiter),
        '%m/%d/%Y{}%H:%M:%S'.format(timeDelimiter),
        '%m-%d-%y{}%H:%M:%S'.format(timeDelimiter),
        '%m-%d-%Y{}%H:%M:%S'.format(timeDelimiter),
        '%Y-%m-%d{}%H:%M:%S'.format(timeDelimiter),
        '%y-%m-%d{}%H:%M:%S'.format(timeDelimiter),
        '%y/%m/%d{}%H:%M:%S'.format(timeDelimiter),
        '%Y/%m/%d{}%H:%M:%S'.format(timeDelimiter),
        '%m/%d/%y{}%H:%M'.format(timeDelimiter),
        '%m/%d/%Y{}%H:%M'.format(timeDelimiter),
        '%m-%d-%y{}%H:%M'.format(timeDelimiter),
        '%m-%d-%Y{}%H:%M'.format(timeDelimiter),
        '%Y-%m-%d{}%H:%M'.format(timeDelimiter),
        '%y-%m-%d{}%H:%M'.format(timeDelimiter),
        '%y/%m/%d{}%H:%M'.format(timeDelimiter),
        '%Y/%m/%d{}%H:%M'.format(timeDelimiter),
        '%d/%m/%Y{}%H:%M'.format(timeDelimiter),
        '%d/%m/%y{}%H:%M'.format(timeDelimiter),
        '%d-%m-%Y{}%H:%M'.format(timeDelimiter),
        '%d-%m-%y{}%H:%M'.format(timeDelimiter),
        
        '%m/%d/%y{}%I:%M:%S%p'.format(timeDelimiter),
        '%m/%d/%Y{}%I:%M:%S%p'.format(timeDelimiter),
        '%m-%d-%y{}%I:%M:%S%p'.format(timeDelimiter),
        '%m-%d-%Y{}%I:%M:%S%p'.format(timeDelimiter),
        '%Y-%m-%d{}%I:%M:%S%p'.format(timeDelimiter),
        '%y-%m-%d{}%I:%M:%S%p'.format(timeDelimiter),
        '%y/%m/%d{}%I:%M:%S%p'.format(timeDelimiter),
        '%Y/%m/%d{}%I:%M:%S%p'.format(timeDelimiter),
        '%d/%m/%Y{}%I:%M:%S%p'.format(timeDelimiter),
        '%d/%m/%y{}%I:%M:%S%p'.format(timeDelimiter),
        
        '%m/%d/%y{}%I:%M:%S %p'.format(timeDelimiter),
        '%m/%d/%Y{}%I:%M:%S %p'.format(timeDelimiter),
        '%m-%d-%y{}%I:%M:%S %p'.format(timeDelimiter),
        '%m-%d-%Y{}%I:%M:%S %p'.format(timeDelimiter),
        '%Y-%m-%d{}%I:%M:%S %p'.format(timeDelimiter),
        '%y-%m-%d{}%I:%M:%S %p'.format(timeDelimiter),
        '%y/%m/%d{}%I:%M:%S %p'.format(timeDelimiter),
        '%Y/%m/%d{}%I:%M:%S %p'.format(timeDelimiter),
        '%d/%m/%Y{}%I:%M:%S %p'.format(timeDelimiter),
        '%d/%m/%y{}%I:%M:%S %p'.format(timeDelimiter),
        
        '%m/%d/%y{}%I:%M%p'.format(timeDelimiter),
        '%m/%d/%Y{}%I:%M%p'.format(timeDelimiter),
        '%m-%d-%y{}%I:%M%p'.format(timeDelimiter),
        '%m-%d-%Y{}%I:%M%p'.format(timeDelimiter),
        '%Y-%m-%d{}%I:%M%p'.format(timeDelimiter),
        '%y-%m-%d{}%I:%M%p'.format(timeDelimiter),
        '%y/%m/%d{}%I:%M%p'.format(timeDelimiter),
        '%Y/%m/%d{}%I:%M%p'.format(timeDelimiter),
        '%y-%m-%d{}%I:%M%p'.format(timeDelimiter),
        '%Y-%m-%d{}%I:%M%p'.format(timeDelimiter),
        
        '%m/%d/%y{}%I:%M %p'.format(timeDelimiter),
        '%m/%d/%Y{}%I:%M %p'.format(timeDelimiter),
        '%m-%d-%y{}%I:%M %p'.format(timeDelimiter),
        '%m-%d-%Y{}%I:%M %p'.format(timeDelimiter),
        '%Y-%m-%d{}%I:%M %p'.format(timeDelimiter),
        '%y-%m-%d{}%I:%M %p'.format(timeDelimiter),
        '%y/%m/%d{}%I:%M %p'.format(timeDelimiter),
        '%Y/%m/%d{}%I:%M %p'.format(timeDelimiter),
        '%y-%m-%d{}%I:%M %p'.format(timeDelimiter),
        '%Y-%m-%d{}%I:%M %p'.format(timeDelimiter),
        ]

    theDate = None
    for fmt in formats:
        try:
            theDate = datetime.strptime(dateString,fmt)
            break
        except Exception as e:
            theDate = None
            
    if theDate == None:
        return None
        
    # if the year is > 2040, assume that '51 means 1951 and subtract 100 years
    if theDate.year >= 2040:
        theDate = theDate.replace(year=theDate.year - 100)
        
    # Make datetime aware
    theDate = timezone(get_time_zone_setting()).localize(theDate)
        
    return theDate.replace(microsecond=0)