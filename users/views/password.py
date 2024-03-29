import hmac
import hashlib
import random


def getPasswordHash(pw :str, theSalt :str | None=None, timesAround='05',encoding='utf-8') -> str | None:
    """Return a string hash of the password or None"""
    from shotglass2.shotglass import get_site_config
    
    if type(pw) is str:
        pw = pw.strip()
        if pw == "":
            return None
            
        if not theSalt:
            theSalt = getPasswordSalt()
        codeWord = str(pw) + theSalt
        
        for i in range(int(timesAround) * 1000):
            codeWord = hmac.new(bytearray(get_site_config()['SECRET_KEY'].encode(encoding)), str(codeWord).encode(encoding), hashlib.sha256).hexdigest() 
        return theSalt +'.'+timesAround+'.'+codeWord
    return None
    
    
def getPasswordSalt():
    return "".join(random.sample('1234567890abcdef',16))
    
    
def matchPasswordToHash(pw,passHash):
    """A helper method to simplify testing a plain text password to a hash.
    Returns either True or False
    """
    
    if pw == None or passHash == None:
        return False
        
    if pw and passHash:
        if type(passHash) is str:
            s = passHash.split('.')
        else:
            return False
            
        if len(s) != 3:
            return False
        salt = s[0]
        timesAround = s[1]
        hashToTest = getPasswordHash(pw,salt,timesAround)
        if hashToTest == passHash:
            return True
        
    return False
    
