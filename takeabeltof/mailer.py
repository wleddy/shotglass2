"""
    My adaptation of flask_mail v 0.9.1
    
    I want to add the ability to use oAuth to connect to gmail SMTP
    servers since they no longer allow login with username and password.


    Original docstring:
    
    flaskext.mail
    ~~~~~~~~~~~~~

    Flask extension for sending email.

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

from flask import render_template_string, render_template
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException, looksLikeEmailAddress
from shotglass2.takeabeltof.mail import Mail, Message


class Mailer:
    """Send an email with the parameters as:
        to_address_list=[list of tuples (recipient name,recipient address)]=None

        If the address_list is not provided, mail will be sent to the admin

        kwargs:
            * body  = <text for body of email> = None
            * body_is_html  = <True | False> = False
            * text_template =<template to render as plain text message> = None
            * html_template =<template to render as html message> = None
            * subject =<subject text (will be rendered with the current context>)>= a default subject
            * subject_prefix =<some text to prepend to the subject = ''
            * from_address =<from address> = sit_config['MAIL_DEFAULT_ADDR']
            * from_sender =<name of sender> = site_config['MAIL_DEFAULT_SENDER']
            * reply_to_address =<reply to address> = from_address
            * reply_to_name =<name of reply to account> = from_sender
            * cc = address list for carbon copy addresses
            * bcc  = address list for blind carbon copy addresses
            * attachment  = < a tuple of data as ("image.png", "image/png", 'data to attach') > = None
            * attachments  = [<list of attachment tuples>] = None
            
        Methods:
            * add_address(*args): add one or more recipients to the email. May be a 2 element tuple of 
            (name,address), a list of tuples, or a string of just an email address, or 2 string arguments,
            name and address.
            * add_cc(*args): add a carbon copy address. Same argument as add_address.
            * add_bcc(*args): add a blind carbon copy address. Same arguments as add_address.
            * add_attachment(attachment): Add one or more attachments to the email
            * send(): Send the email. Sets the result properties below.

        Result properties:
            * self.success <bool> False | True if sent
            * self.result_text <"some message">
    """

    def __init__(self,address_list=[],**kwargs):
        # import pdb;pdb.set_trace()
        self._to = []
        # some old code will set address_to to None
        if address_list == None:
            address_list = []
            
        self.add_address(address_list)
        
        site_config = get_site_config() 
        self.admin_name = site_config['MAIL_DEFAULT_SENDER']
        self.admin_addr = site_config['MAIL_DEFAULT_ADDR']
        self.kwargs = kwargs # templates may need values here...
        self.body = kwargs.get('body',None)
        self.body_is_html = kwargs.get('body_is_html',None)
        self.text_template = kwargs.get('text_template',None)
        self.html_template = kwargs.get('html_template',None)
        self.subject_prefix = kwargs.get('subject_prefix',site_config.get("MAIL_SUBJECT_PREFIX",''))
        self.from_address = kwargs.get('from_address',self.admin_addr)
        self.from_sender = kwargs.get('from_sender',self.admin_name)
        self.reply_to = kwargs.get('reply_to',self.from_address)
        self._cc = kwargs.get('cc',[])
        self._bcc = kwargs.get('bcc',[])
        self._attachments = []
        self.subject = kwargs.get('subject','').strip()
        # appends all attachments regardless of keyword used
        self.add_attachment(kwargs.get('attachments',None))
        self.add_attachment(kwargs.get('attachment',None))
        
        self.success = False
        self.result_text = 'initialized'
   
    def _add_to_address_list(self,target,*args,address_only=False):
        """The args may be:
                * 2 strings like: 'Joe Smith','joe@example.com'
                * a tuple like: ('Joe Smith','joe@example.com')
                * a list of tuples like: [('Joe Smith','joe@example.com'), ... ('Jane Smith','jane@example.com'),]
            
            Normally, tries to create a tuple of (name,address) to add to the list.
            
            if address_only is True, add the email address only to the list
        """
        # import pdb;pdb.set_trace()
        
        if target == None:
            target = []
        if not isinstance(target,list):
            target = [target]
            
        temp_address_list = []
            
        if len(args) == 2 and isinstance(args[0],str) and isinstance(args[1],str):
            #assume that these are name, address as str
            temp_address_list.append((args[0],args[1]))
        elif len(args) == 1 and isinstance(args[0],str):
            temp_address_list.append((args[0],args[0]))
        else:
            for arg in args:
                if isinstance(arg,tuple):
                    if len(arg) >= 2: 
                        temp_address_list.append(arg[:2])
                    elif len(arg) == 1:
                        temp_address_list.append((arg,arg))

                elif isinstance(arg,list):
                    for item in arg:
                        if isinstance(item,tuple):
                            temp_address_list.append(item)
                        elif isinstance(item,str):
                                temp_address_list.append((item,item))
                            
                elif isinstance(arg,str):
                    temp_address_list.append((arg,arg))
            
        for x in range(len(temp_address_list)):
            # try to put the tuples in the correct order if possible
            name = temp_address_list[x][0]
            address = temp_address_list[x][1]

            if not looksLikeEmailAddress(address) and looksLikeEmailAddress(name):
                # swap values
                temp_address_list[x] = (address,name)
            
            if address_only:
                temp_address_list[x] = temp_address_list[x][1]
                    
        #finally, add the new address(s) to the target list
        target.extend(temp_address_list)
            
            
    def add_address(self,*args):
        """Add one or more recipients to the email.
        """
        self._add_to_address_list(self._to,*args)
            
    def add_cc(self,*args):
        self._add_to_address_list(self._cc,*args,address_only=True)

    def add_bcc(self,*args):
        self._add_to_address_list(self._bcc,*args,address_only=True)
        
        
    def add_attachments(self,attachments):
        """just a wrapper for add_attachment"""
        self.add_attachment(attachments)
        
        
    def add_attachment(self,attachment):
        """Add one or more attachments to the email.
        
        Each attachment consists of 3 elements, ideally as a tuple but may be a list of tuples:
            1 File name: Name to use when attachment is delivered.
            2 mime type: The mime type of the attachment.
            3 content: The data to attach.
        
        """
        
        def _append_attachment(attachment):
            # add a tuple to self._attacments
            if isinstance(attachment,tuple) and len(attachment) == 3:
                self._attachments.append(attachment)
                
        # housekeeping... self._attachments must be a list
        if self._attachments:
            if not isinstance(self._attachments,list):
                self._attachments = [self._attachments]
        else:
            self._attachments = []
        
        # is attachment a list? Step through them and
        if isinstance(attachment,list):
            for item in attachment:
                _append_attachment(item)
        else:
            _append_attachment(attachment)


    def _set_result(self,success,mes):
        self.success = success
        self.result_text = mes


    def send(self):
        outgoing = Mail()

        sent_cnt = 0
        err_cnt = 0
        err_list = []
        result = True
        # import pdb;pdb.set_trace()
        if not self._to:
            self._to = [(self.admin_name,self.admin_addr),]

        for recipient in self._to:
            name = ""
            address = ""
            body_err_head = ""
            if isinstance(recipient,tuple):
                if len(recipient) == 1:
                    # extend recipient
                    recipient = recipient[0] + (recipient[0],)
                name = recipient[0]
                address = recipient[1]
            else:
                address = recipient #assume its a str
                name = recipient

            if not looksLikeEmailAddress(address) and looksLikeEmailAddress(name):
                # swap values
                temp = address
                address = name
                name = temp
            if not looksLikeEmailAddress(address):
                # still not a good address...
                address = self.admin_addr
                name = self.admin_name
                if not self.body:
                    self.body = ""

                body_err_head = "**Bad Address**: {}\r\r".format(recipient,)
                
            if not self.subject:
                self.subject = 'A message from {}'.format(self.from_sender).strip()
            self.subject = '{} {}'.format(self.subject_prefix,self.subject).strip()
            self.subject = render_template_string(self.subject.strip(), **self.kwargs)
            #Start a message
            msg = Message( self.subject,
                          sender=(self.from_sender, self.from_address),
                          recipients=[(name, address)],
                          cc=self._cc,
                          bcc=self._bcc,
                          )

            #Get the text body verson
            if self.body:
                if self.body_is_html:
                    msg.html = render_template_string("{}{}".format(body_err_head,self.body,), **self.kwargs)
                else:
                    msg.body = render_template_string("{}{}".format(body_err_head,self.body,), **self.kwargs)
            if self.html_template:
                msg.html = render_template(self.html_template, **self.kwargs)
            if self.text_template:
                msg.body = render_template(self.text_template, **self.kwargs)
            if not msg.body and not msg.html:
                self._set_result(False,'Message contained no body content.')
                return

            msg.reply_to = self.reply_to

            if self._attachments:
                for attachment in self._attachments:
                    if attachment and len(attachment) > 2:
                        msg.attach(attachment[0],attachment[1],attachment[2])

            try:
                outgoing.send(msg)
                sent_cnt += 1
            except Exception as e:
                mes = "Error Sending email"
                printException(mes,"error",e)
                err_cnt += 1
                err_list.append("Error sending message to {} err: {}".format(recipient,str(e)))

        # End Loop
        if sent_cnt == 0:
            mes = "No messages were sent."
            result = False
        else:
            mes = "{} messages sent successfully.".format(sent_cnt)
        if err_cnt > 0:
            result = False
            mes = mes + " {} messages had errors.\r\r{}".format(err_cnt,err_list)

        self._set_result(result, mes)
            
            
def send_message(to_address_list=None,**kwargs):
    """Wrapper for the class to conform with the old function call"""
        
    mailer = Mailer(to_address_list,**kwargs)
    mailer.send()
    
    return (mailer.success,mailer.result_text)
    
    
def email_admin(subject=None,message=None):
    """
        Shortcut method to send a quick email to the admin
    """
    try:
        site_config = get_site_config()
        if not subject:
            subject = "An alert was sent from {}".format(site_config['SITE_NAME'])
        
        if not message:
            message = "An alert was sent from {} with no message...".format(site_config['SITE_NAME'])
        
        return send_message(
                None,
                subject=subject,
                body = message,
                )
    except Exception as e:
        mes = "Not able to send message to admin."
        printException(mes,err=e)
        return (False,mes)
    
        
def alert_admin(subject=None,message=None):
    # just an alias to email admin
    # usually just ignore the return
    return email_admin(subject,message)
    
    