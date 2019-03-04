# takeabeltof.date_utils.py

Some utilities to handle dates.

---
> #### date_to_string(*value,format*): => str

Attempt to return a date string in the format specified. value may be a datetime or a 'date like' string.

A number of "shortcut" formats are defined:

```
    'date':"03/04/19",
    
    'date_full_year': "03/04/2019",
    
    'time':'06:30',
    
    'time_long':'06:30:22',
    
    'ampm': 'AM' | 'PM',
    
    'local_time': '6:20PM',
    
    'iso_date': '2019-03-04'
    
```

---
> #### datetime_as_string(*the_datetime=None*): => str

Return a string version of the datetime provided or for now.

---
> #### getDatetimeFromString(*dateString*): => datetime

Try to create a datetime object based on the 'date like' string provided or else None.
The datetime object returned is time zone aware

---
> #### get_time_zone_setting(): = str or None

Return the TIME_ZONE config setting if it exists else None

---
> #### local_datetime_now(*time_zone=None*): => datetime

Return a datetime object for now at the time zone specified. This is a time zone aware version of datetime.now().
    
If time_zone is None, use the TIME_ZONE name from date_utils.get_time_zone_setting() else use the local time per the server

---
> #### make_tz_aware(*the_datetime,time_zone=None*): => datetime

Return the time zone aware version of the datetime 

This function will NOT convert an aware datetime to a new time zone.

---
> #### nowString(): => str

Returns the current datetime as a string. A short cut to datetime_as_string()

---
[Return to Docs](/docs/shotglass2/README.md)
