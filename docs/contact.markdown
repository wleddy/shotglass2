# How Contacts Works

The contacts module is part of takeabeltof package. The goal is to provide a customizable visitor contact form that will
be emailed to the designated user.


## class ContactForm(namedlist):

The ContactForm class will provide the information needed to create the input form, validate input and submit it for email

### Properties:

* form_fields - The namedlist object that contains the field properties and data
    * title = None
    * type = "text" - ([text | num | date]|textarea)
    * size - a tuple of (cols,rows)
    * value= "" - a text value
    * placeholder_text = '' - prompt text to display or ""
    * is_from_name=False - True if this field is the field containing the sender name
    * is_from_address=False - True if this field is the field containing the sender email address
* additional properties
    * to_name = contact name|admin name | None
    * to_address = contact address | admin address | None
    * reply_to_name = from_name
    * reply_to_address = from_address
    * email_template_path = contact/contact_email.md
    * form_template_path = contact/contact_form.html
    * form_page_head = "Some default text" - Some text to place at top of form page. Assumed to be markdown.
    * subject = "A contact request from <site name>"
    * contact_form = html for contact form rendered from ContactFields list.
    * email_body = email body as rendered from template

### functions:

* __init__(self, **kwargs)
    * contact_fields = None | a list of dicts{title,size,value,help_text,is_from_name,is_from_address}
    * to_name = default
    * to_address = default
    * reply_to_name = default
    * reply_to_address = default
    * email_template_path = default
    * form_template_path = default
    * form_page_head = default
    * subject = default
    
* _make_fields_list(self, self.contact_fields)
* to(self)  
    return a tuple of (name,addr) for the recipient
* from(self)
    * return a tuple of (name,addr) for the sender
* reply_to(self)
    * return a tuple of (name,addr) for the reply to 
* display_form(self)
    * return html form to display
* send_email(self)
    * call .mailer.send_message() and return result and message