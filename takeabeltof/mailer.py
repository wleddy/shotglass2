from flask import g, flash, render_template_string, render_template
from flask_mail import Message
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, looksLikeEmailAddress

def send_message(to_address_list=None,**kwargs):
    """Send an email with the parameters as:
        to_address_list=[list of tuples (recipient name,recipient address)]=None
        
        If the to_address_list is not provided, mail will be sent to the admin
        
        kwargs:
            * body  = <text for body of email> = None
            * body_is_html  = <True | False> = False
            * text_template =<template to render as plain text message> = None
            * html_template =<template to render as html message> = None
            * subject =<subject text (will be rendered with the current context>)>= a default subject
            * subject_prefix =<some text to prepend to the subject = ''
            * from_address =<from address> = sit_config['MAIL_DEFAULT_ADDR']
            * from_sender =<name of sender> = site_config['MAIL_DEFAULT_SENDER']
            * reply_to_address =<replyto address> = from_address
            * reply_to_name =<name of reply to account> = from_sender
            * cc = address list for carbon copy addresses
            * bcc  = address list for blind carbon copy addresses
            * attachment  = < a tuple of data as ("image.png", "image/png", 'data to attach') > = None
            * attachments  = [<list of attachment tuples>] = None
            
        On completion returns a tuple of:
            ( success [`True` or `False`], message <"some message">)
    """
    #import pdb;pdb.set_trace()
    from app import mail
    
    site_config = get_site_config() #update the settings. this also recreates the mail var in app with new settings
    
    body = kwargs.get('body',None)
    body_is_html = kwargs.get('body_is_html',None)
    text_template = kwargs.get('text_template',None)
    html_template = kwargs.get('html_template',None)
    subject_prefix = kwargs.get('subject_prefix',site_config.get("MAIL_SUBJECT_PREFIX",''))
    attachment = kwargs.get('attachment',None)
    attachments = kwargs.get('attachments',None)
    
    if attachments:
        if not isinstance(attachments,list):
            attachments = [attachments]
        attachments.extend([attachment])
    elif attachment:
        attachments = [attachment]
    
    try:
        admin_addr = site_config['MAIL_DEFAULT_ADDR']
        admin_name = site_config['MAIL_DEFAULT_SENDER']
    except KeyError as e:
        mes = "MAIL Settings not found"
        mes = printException(mes,'error',e)
        return (False, mes)
    
    from_address = kwargs.get('from_address',admin_addr)
    from_sender = kwargs.get('from_sender',admin_name)
    reply_to = kwargs.get('reply_to',from_address)
    cc = kwargs.get('cc',None)
    bcc = kwargs.get('bcc',None)
        
    subject = subject_prefix + ' ' +kwargs.get('subject','A message from {}'.format(from_sender)).strip()
    
    if not text_template and not html_template and not body:
        mes = "No message body was specified"
        printException(mes,"error")
        return (False, mes)
        
    if not to_address_list or len(to_address_list) == 0:
        #no valid address, so send it to the admin
        to_address_list = [(admin_name,admin_addr),]
        
    with mail.record_messages() as outbox:
        sent_cnt = 0
        err_cnt = 0
        err_list = []
        result = True
        for who in to_address_list:
            #import pdb;pdb.set_trace()
            name = ""
            address = ""
            body_err_head = ""
            if type(who) is tuple:
                if len(who) == 1:
                    # extend whp
                    who = who[0] + (who[0],)
                name = who[0]
                address = who[1]
            else:
                address = who #assume its a str
                name = who
                
            if not looksLikeEmailAddress(address) and looksLikeEmailAddress(name):
                # swap values
                temp = address
                address = name
                name = temp
            if not looksLikeEmailAddress(address):
                # still not a good address...
                address = admin_addr
                name = admin_name
                if not body:
                    body = ""
                    
                body_err_head = "Bad Addres: {}\r\r".format(who,)
                
            subject = render_template_string(subject.strip(), **kwargs)
            #Start a message
            msg = Message( subject,
                          sender=(from_sender, from_address),
                          recipients=[(name, address)],
                          cc=cc,
                          bcc=bcc,
                          )
    
            #Get the text body verson
            if body:
                if body_is_html:
                    msg.html = render_template_string("{}{}".format(body_err_head,body,), **kwargs)
                else:
                    msg.body = render_template_string("{}{}".format(body_err_head,body,), **kwargs)
            if html_template:
                msg.html = render_template(html_template, **kwargs)
            if text_template:
                msg.body = render_template(text_template, **kwargs) 
            
            msg.reply_to = reply_to
           
            if attachments:
                for attachment in attachments:
                    if attachment and len(attachment) > 2:
                        msg.attach(attachment[0],attachment[1],attachment[2])
                    
            try:
                mail.send(msg)
                sent_cnt += 1
            except Exception as e:
                mes = "Error Sending email"
                printException(mes,"error",e)
                err_cnt += 1
                err_list.append("Error sending message to {} err: {}".format(who,str(e)))

        # End Loop
        if sent_cnt == 0:
            mes = "No messages were sent."
            result = False
        else:
            mes = "{} messages sent successfully.".format(sent_cnt)
        if err_cnt > 0:
            mes = mes + " {} messages had errors.\r\r{}".format(err_cnt,err_list)
            
        return (result, mes)
            
            
            
def email_admin(subject=None,message=None):
    """
        Shortcut method to send a quick email to the admin
    """
    try:
        site_config = get_site_config()
        if subject == None:
            subject = "An alert was sent from {}".format(site_config['SITE_NAME'])
        
        if message == None:
            message = "An alert was sent from {} with no message...".format(site_config['SITE_NAME'])
        
        return send_message(
                None,
                subject=subject,
                body = message,
                )
    except Exception as e:
        flash(printException("Not able to send message to admin.",str(e)))
    
        
def alert_admin(subject=None,message=None):
    # just an alias to email admin
    # usually just ignore the return
    return email_admin(subject,message)
    
    