# takeabeltof.jinja_filters.py

Some custom filters to use in templates

---
> #### iso_date_string(*value*): => str 

Returns a string formatted like a date as 'yyyy-mm-dd'. Value may be a datetime or a 'date like' string.

---
> #### short_date_string(*value*): => str

Returns a string formatted like a date in "'merican" style as 'mm/dd/yy'. Value may be a datetime or a 'date like' string.

---
> #### long_date_string(*value*): => str

Returns a string formatted like a date as 'Month_name, d, yyyy'. Value may be a datetime or a 'date like' string.

---
> #### two_decimal_string(value): => str

Return a string representation of the value as a number with 2 decimal places. Value may be a number or a string.

---
> #### money(value): => str

An alias to two_decimal_string().

---
> #### register_jinja_filters(app): => Nothing

Registers the filters with app.

---

[Return to Docs](/docs/takeabeltof/README.md)
