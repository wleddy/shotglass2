import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import pytest
from app import app
import shotglass2.takeabeltof.utils as utils
from werkzeug.exceptions import HTTPException

def test_cleanRecordID():
    """Tesst the cleanRecordID utility fuction"""
    
    assert utils.cleanRecordID(1234) == 1234
    assert utils.cleanRecordID("1234") == 1234
    assert utils.cleanRecordID("this is a test4455") == -1
    assert utils.cleanRecordID("1234this is a test") == -1
    assert utils.cleanRecordID(-4) == -4
    assert utils.cleanRecordID('-4') == -1
    assert utils.cleanRecordID(None) == -1
    

def test_looksLikeEmailAddress():
    """Does this string look like an email address?"""
    assert utils.looksLikeEmailAddress("bill@example.com")
    assert utils.looksLikeEmailAddress("bill.leddy@example.com")
    assert utils.looksLikeEmailAddress() != True
    assert utils.looksLikeEmailAddress(2343345) != True
    assert utils.looksLikeEmailAddress("@Exmaple.com") != True
    assert utils.looksLikeEmailAddress("bill@example") != True
    
    
def test_printException():
    with app.app_context():
        # printException((mes="An Unknown Error Occured",level="error",err=None))
        assert utils.printException(mes="Not an error") == "Not an error"
        # create an acutal error
        with pytest.raises(Exception):
            try:
                if nothing == True:
                    pass
            except Exception as e:
                mes =  utils.printException(mes="Should Be error",err=e)
                assert "NameError" in mes
            
def test_render_markdown_for():
    with app.app_context():
        from flask import Blueprint, g
        from shotglass2 import shotglass
        shotglass.set_template_dirs(app)
        mod = Blueprint('testme',__name__) 
        result = utils.render_markdown_for('test_script.md',mod)
        assert "no file found" in result
        result = utils.render_markdown_for('takeabeltof.md',mod)
        assert "no file found" not in result
        assert "<h1>Takeabeltof</h1>" in result
    
def test_render_markup_text():
    with app.app_context():
        result = utils.render_markdown_text("## Now is the time")
        assert "<h2>Now is the time</h2>" in result
        
        
def test_handle_request_error():
    #handle_request_error(error=None,request=None,level='info')
    with app.app_context():
        from shotglass2.takeabeltof.utils import handle_request_error
        error = HTTPException()
        error.code=404
        result = handle_request_error(error,None)
        assert "Request status: 404" in result
        
        
def test_formatted_phone_number():
    # test the results of attempst to format a phone number
    assert utils.formatted_phone_number('916-444-2904') == '916-444-2904'
    assert utils.formatted_phone_number('(916) 444-2904') == '916-444-2904'
    assert utils.formatted_phone_number('9164442904') == '916-444-2904'
    assert utils.formatted_phone_number('(916)444-2904') == '916-444-2904'
    assert utils.formatted_phone_number('444-2904') == ''
    assert utils.formatted_phone_number('Not a number') == ''
    assert utils.formatted_phone_number('(916)444-2904','/') == '916/444/2904'
    assert utils.formatted_phone_number('(916)444-2904',raw=True) == ('916','444','2904','') # returns 4 items
