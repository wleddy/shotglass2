# takeabeltof.mailer.py

Utility to send email. What a shocker!

---
> #### send_message(*to_address_list=None,**kwargs*): => (bool, str)

Send an email with the parameters as:
    > to_address_list=[list of tuples (recipient name,recipient address)]=None
    > 
    > If the to_address_list is not provided, mail will be sent to the admin
    > 
    > -- all templates must use 'context' as their only context variable
    > **kwargs:
    >     context = {a dictionary like object with data for rendering all emails} = {}
    >     body = <text for body of email> = None
    >     body_text_is_html = <True | False> = False
    >     text_template=<template to render as plain text message> = None
    >     html_template=<template to render as html message> = None
    >     subject=<subject text (will be rendered with the current context>)>= a default subject
    >     subject_prefix=<some text to prepend to the subject: = ''
    >     from_address=<from address> = site_config['MAIL_DEFAULT_ADDR']
    >     from_sender=<name of sender> = site_config['MAIL_DEFAULT_SENDER']
    >     reply_to_address=<replyto address> = from_address
    >     reply_to_name=<name of reply to account> = from_sender
    >     
    > On completion returns a tuple of:
    >     success [True or False]
    >     message "some message"

---
> #### email_admin(subject=None,message=None): => (bool, str)

Shortcut method to send a quick email to the admin

---
> #### alert_admin(subject=None,message=None): => (bool, str)

An alias to email_admin() for reasons I don't recall...

---
[Return to docs](/docs/takeabeltof/index.md)