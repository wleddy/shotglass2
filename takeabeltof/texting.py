"""Handle outgoing and incoming text messages
  using Twilio service.
  
  The account information needs to be in the site configuration as
  a dict like this:
  
  ## Set up the Twilio texting configuration
  TWILIO_CONFIGURATION = {
      'acct_sid':'<account SID>',
      'auth_token':'<authorization token>',
      'phone_number':'<your FROM phone number>',
      }
      
  Inflict this on an un-wary public like so...
  text = TextMessage(to_phone_number,messag_to_send)
  text.send()
  if not text.success:
      email_admin('Texting Error Occurred',text.result_text)
  
"""
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import printException
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.twiml.messaging_response import MessagingResponse


class TextMessage():
    def __init__(self,to_number="",message=""):
        self.to_number = to_number.strip()
        self.message = message.strip()
        self.success = True
        self.result_text = ''
        self._acct_sid = ''
        self._auth_token = ''
        self._from_number = ''
        self._set_config()
        self.send_result = None
        
    def send(self,to_number="",message=""):
        """Actually send a text"""
        
        if to_number:
            self.to_number = to_number.strip()
            
        if message:
            self.message = message.strip()
            
        if not self.success:
            return # something is not right...
        if not self.validate_phone_number(self._from_number):
            return # success is False and result_text is set
        client = self._get_client()
        if client:
            if not self.validate_phone_number(self.to_number):
                return # success is False and result_text is set
            if not self.message:
                self.success = False
                self.result_text = "The message may not be empty"
                return
            
            try:
                # return a twilio message object
                # It looks like if the message fails, client just errors out and self.send_result is not updated
                self.send_result = client.messages.create(body=self.message,from_=self._from_number,to=self.to_number)
            except TwilioRestException as e:
                self.success = False
                self.result_text = str(e)
                printException(self.result_text,'error',err=e)                
                    
        
    def _get_client(self):
        client = None
        try:
            client = Client(self._acct_sid,self._auth_token)
        except Exception as e:
            self.success = False
            self.result_text = "Error while attempting to create Twilio Client"
            printException(self.result_text,'error',err=e)
            
        return client
        
        
    def validate_phone_number(self,phone_number):
        """Try to determine is phone_number is valid
            At the end, if succesful phone_number will contain a clean phone #
        """
        temp_number = ''
        if not isinstance(phone_number,str):
            self.success = False
            self.result_text = "Invalid phone number: {}".format(phone_number)
            return False
            
        if not phone_number.strip():
            self.success = False
            self.result_text = "Phone number may not be empty"
            return False
            
        if phone_number.strip()[0:2] == "+1":
            # remove the plus sign if there
            temp_number = phone_number.strip()[2:]
        else:
            temp_number = phone_number.strip()
            
        #remove non-numeric chars
        clean_number = ''
        for s in temp_number:
            if not s.isnumeric():
                continue
            clean_number += s
            
        temp_number = clean_number
        
        if len(temp_number) != 10:
            self.success = False
            self.result_text = "Phone number '{}' is not the correct length".format(phone_number)
            return False
            
        # Ok, we have what may be a phone number...
        phone_number = temp_number
        
        return True
        
        
    def _set_config(self):
        try:
            client_config = get_site_config()['TWILIO_CONFIGURATION'] # returns a dict
                
            if not isinstance(client_config,dict):
                raise RuntimeError
                
            if not self._acct_sid:
                self._acct_sid = client_config['acct_sid']
            if not self._auth_token:
                self._auth_token = client_config['auth_token']
            if not self._from_number:
                self._from_number = client_config['phone_number']
                if not self.validate_phone_number(self._from_number):
                    raise RuntimeError
                    
        except Exception as e:
            self.success = False
            self.result_text = "Error while fetching Twilio configuration"
            printException(self.result_text,'error',err=e)
        
                
class TextResponse():
    """Create a response object for Twilio web hook request"""
    
    def __init__(self):
        self.response = MessagingResponse()
        self.message = None 
        self.success = True
        self.result_text = ''
    
    
    def create_message(self,message_to_send='',**kwargs):
        if message_to_send and isinstance(message_to_send,str):
            msg = self.response.message(message_to_send.strip())
            self.message = self.response
        else:
            self.message = None
            self.success = False
            self.result_text = "The message must not be empty"
