import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import pytest
from datetime import datetime
import shotglass2.takeabeltof.date_utils as dates
from shotglass2.shotglass import get_site_config

def test_local_datetime_now():
    site_config = get_site_config()
    #site_config['TIME_ZONE'] = 'US/Pacific'
    now = datetime.now()
    local_now = dates.local_datetime_now()
    assert now.day == local_now.day
    assert now.hour == local_now.hour
    assert now.month == local_now.month
    assert local_now.tzinfo is not None
    assert local_now.tzinfo.zone == site_config["TIME_ZONE"]
    
    # spcecify a time zone
    zone = "US/Eastern"
    east_now = dates.local_datetime_now(zone)
    assert east_now.tzinfo is not None
    assert east_now.tzinfo.zone == zone
    
    
def test_make_tz_aware():
    # make_tz_aware(the_datetime,time_zone=None)
    site_config = get_site_config()
    
    zone = site_config["TIME_ZONE"]
    aware = dates.make_tz_aware(datetime.now(),zone)
    now = dates.local_datetime_now()
    assert aware.tzinfo.zone == zone
    aware = dates.make_tz_aware(datetime.now())
    assert aware.tzinfo.zone == site_config["TIME_ZONE"]
    
    
def test_get_time_zone_setting():
    site_config = get_site_config()
    
    zone = dates.get_time_zone_setting()
    assert zone is not None
    assert zone == site_config["TIME_ZONE"]
    
    
def test_date_to_string():
    assert len(dates.date_to_string(dates.local_datetime_now(),"%Y-%m-%d")) == 10
    assert len(dates.date_to_string("11/15/18","%Y-%m-%d")) == 10


def test_nowString():
    # This is really an alias to datetime_as_string
    site_config = get_site_config()
    
    site_config['TIME_ZONE'] = 'US/Pacific'

    now = dates.nowString()
    assert now == dates.datetime_as_string(datetime.now())
    
    
def test_datetime_as_string():
    now = datetime.now()
    assert dates.datetime_as_string(now) == now.isoformat(sep=" ")[:19]
    
    
def test_getDatetimeFromString():
    site_config = get_site_config()
    
    assert dates.getDatetimeFromString("12/14/12") == dates.make_tz_aware(datetime(2012,12,14),site_config["TIME_ZONE"])
    assert dates.getDatetimeFromString("2012-12-14") == dates.make_tz_aware(datetime(2012,12,14),site_config["TIME_ZONE"])
    assert dates.getDatetimeFromString("12/14/2012") == dates.make_tz_aware(datetime(2012,12,14),site_config["TIME_ZONE"])
    assert dates.getDatetimeFromString("2/8/19") == dates.make_tz_aware(datetime(2019,2,8),site_config["TIME_ZONE"])
    assert dates.getDatetimeFromString("2/8/51") == dates.make_tz_aware(datetime(1951,2,8),site_config["TIME_ZONE"])
  