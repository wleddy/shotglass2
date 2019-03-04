# takeabeltof.jinja_filters.py

Some custom filters to use in templates

---
> #### iso_date_string(*value*): => str 

Returns a string formatted like a date as 'yyyy-mm-dd'. Value may be a datetime or a 'date like' string.

---
> #### short_date_string(*value*): => str

Returns a string formatted like a date in "'merican" style as 'mm/dd/yy'. Value may be a datetime or a 'date like' string.

---
> #### short_day_and_date_string(*value*): => str

Returns a string formatted like a date like 'Mon. 3/4/19'. Value may be a datetime or a 'date like' string.

---
> #### abbr_date_string(*value*): => str

Returns a string formatted like a date like 'Mar. 3, 2019'. Value may be a datetime or a 'date like' string.

---
> #### short_abbr_date_string(*value*): => str

Returns a string formatted like a date like 'Mar. 3'. Value may be a datetime or a 'date like' string.

---
> #### long_date_string(*value*): => str

Returns a string formatted like a date as 'Month Name, d, yyyy'. Value may be a datetime or a 'date like' string.

---
> #### local_date_string(*value*): => str

Returns a string formatted like a date as '3/1/19'. Value may be a datetime or a 'date like' string.

---
> #### local_time_string(*value*): => str

Returns the time formatted as '6:00AM'. Value may be a datetime or a 'datetime like' string.

---
> #### two_decimal_string(value): => str

Return a string representation of the value as a number with 2 decimal places. Value may be a number or a string.

---
> #### money(value): => str

An alias to two_decimal_string().

---
> #### weblink(address,safe=True,blank=True): => str

Returns a html anchor object based on address. If `safe` is False the text will be escaped prior to diaplay. If 
`blank` is True the link opens in a new window.

The link text will be a "simplified" version of a web link. e.g. 'http://example.com/' will render
as:

    `<a href="http://example.com/" target="_blank" >example.com</a>`

---
> #### register_jinja_filters(app): => Nothing

Registers the filters with app.

---

[Return to Docs](/docs/shotglass2/README.md)
