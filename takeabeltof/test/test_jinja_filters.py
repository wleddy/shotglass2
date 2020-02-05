import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.
from datetime import datetime
import shotglass2.takeabeltof.jinja_filters as filters

def test_two_digit():
    """Test that it rounds to 2 digits"""
    assert filters.two_decimal_string(1234.0) == "1234.00"
    assert filters.two_decimal_string(1234) == "1234.00"
    assert filters.two_decimal_string(1234.001) == "1234.00"
    assert filters.two_decimal_string(1234) == "1234.00"
    assert filters.two_decimal_string("1234") == "1234.00"
    assert filters.two_decimal_string(1234.9999) == "1234.99"
    assert filters.two_decimal_string("1234.1") == "1234.10"
    assert filters.two_decimal_string("") == "0.00"
    assert filters.two_decimal_string(None) == "0.00"
    
def test_short_date_string():
    test_date = datetime(2018,5,9)
    assert filters.short_date_string(test_date) == "05/09/18"
    assert filters.short_date_string("2018-05-09") == "05/09/18"
    assert filters.short_date_string("05/09/18") == "05/09/18"

def test_short_day_and_date_string():
    test_date = datetime(2018,5,9,6,33,15)
    assert filters.short_day_and_date_string(test_date) == "Wed. 5/9/18"

def test_short_day_and_date_and_time_string():
    test_date = datetime(2018,5,9,6,33,15)
    assert filters.short_day_and_date_and_time_string(test_date) == "Wed. 5/9/18 6:33AM"
    test_date = datetime(2018,5,9,14,33,15)
    assert filters.short_day_and_date_and_time_string(test_date) == "Wed. 5/9/18 2:33PM"
    

def test_long_date_string():
    test_date = datetime(2018,5,9)
    assert filters.long_date_string(test_date) == "May 9, 2018"
    assert filters.long_date_string("2018-05-09") == "May 9, 2018"
    assert filters.long_date_string("05/09/18") == "May 9, 2018"

    
def test_iso_date_string():
    test_date = datetime(2018,5,9)
    assert filters.iso_date_string(test_date) == "2018-05-09"
    assert filters.iso_date_string("2018-05-09") == "2018-05-09"
    assert filters.iso_date_string("05/09/18") == "2018-05-09"

def test_local_date_string():
    test_date = datetime(2018,5,9)
    assert filters.local_date_string(test_date) == "5/9/18"
    assert filters.local_date_string("2018-05-09") == "5/9/18"
    assert filters.local_date_string("05/09/18") == "5/9/18"
    assert filters.local_date_string("5/9/18") == "5/9/18"
    
def test_local_date_and_time_string():
    test_date = datetime(2018,5,9,6,33,15)
    assert filters.local_date_and_time_string(test_date) == "5/9/18 6:33AM"
    test_date = datetime(2018,5,9,18,33,15)
    assert filters.local_date_and_time_string(test_date) == "5/9/18 6:33PM"
    # should return text un-altered
    assert filters.local_date_and_time_string("this is a test") == "this is a test"

def test_excel_date_and_time_string():
    test_date = datetime(2018,5,9,6,33,15)
    assert filters.excel_date_and_time_string(test_date) == "5/9/18 6:33 AM"
    test_date = datetime(2018,5,9,18,33,15)
    assert filters.excel_date_and_time_string(test_date) == "5/9/18 6:33 PM"
    # should return text un-altered
    assert filters.excel_date_and_time_string("this is a test") == "this is a test"

def test_abbr_date_string():
    test_date = datetime(2019,5,9)
    assert filters.abbr_date_string(test_date) == "Thu. May 9, 2019"
    assert filters.abbr_date_string("2018-05-09") == "Wed. May 9, 2018"
    assert filters.abbr_date_string("05/09/18") == "Wed. May 9, 2018"
    assert filters.abbr_date_string("5/9/18") == "Wed. May 9, 2018"
    test_date = datetime(2019,6,9)
    assert filters.abbr_date_string(test_date) == "Sun. Jun. 9, 2019"
    assert filters.abbr_date_string("2019-06-09") == "Sun. Jun. 9, 2019"
    assert filters.abbr_date_string("06/09/19") == "Sun. Jun. 9, 2019"
    assert filters.abbr_date_string("6/9/19") == "Sun. Jun. 9, 2019"
    
    
def test_render_markdown():
    import app
    with app.app.app_context():
        assert filters.render_markdown("# This is a test") == "<h1>This is a test</h1>\n"
    
def test_default_if_none():
    assert filters.default_if_none(None) == ''
    assert filters.default_if_none(None,'Ok') == 'Ok'
    assert filters.default_if_none(0,'Ok') == 0
    assert filters.default_if_none(0,'Ok',True) == 'Ok'
    assert filters.default_if_none(None,'Ok',True) == 'Ok'
    
