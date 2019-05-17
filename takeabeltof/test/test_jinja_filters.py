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
    
def abbr_date_string():
    test_date = datetime(2019,5,9)
    assert filters.abbr_date_string(test_date) == "Thu. May 9, 2019"
    assert filters.abbr_date_string("2018-05-09") == "Thu. May 9, 2019"
    assert filters.abbr_date_string("05/09/18") == "Thu. May 9, 2019"
    assert filters.abbr_date_string("5/9/18") == "Thu. May 9, 2019"
    test_date = datetime(2019,6,9)
    assert filters.abbr_date_string(test_date) == "Sun. Jun. 9, 2019"
    assert filters.abbr_date_string("2019-06-09") == "Sun. Jun. 9, 2019"
    assert filters.abbr_date_string("06/09/19") == "Sun. Jun. 9, 2019"
    assert filters.abbr_date_string("6/9/19") == "Sun. Jun. 9, 2019"
    
