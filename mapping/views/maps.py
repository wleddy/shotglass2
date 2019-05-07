## Map view of trips
from flask import g, redirect, url_for, \
     render_template, flash, Blueprint, request
from shotglass2.takeabeltof.utils import printException
import json
from datetime import timedelta
from shotglass2.takeabeltof.date_utils import getDatetimeFromString, local_datetime_now

mod = Blueprint('map', __name__,template_folder='templates/map', url_prefix='/map', static_folder='static')

def setExits():
    g.title = 'Maps'
    
def simple_map(map_data,target_id="map",marker_template=None,**kwargs):
    """Return an html snippet with code for a map with one or more markers
    param: map_data, a list of dicts of:
        lat: Latitude
        lng: What do you think?
    optional data;
        UID: unique identifier for the point.
        location_name,
        title: The title for the marker
        description: a description, may be markdown
        
    param: target_id = optional id of html object that will hold the map. defaults to "map"
    param: marker_template = The path to the template to use to render the marker popup. Defaults to None
    
    Returns the javascript text and data to embed into a page, not the page itself.
    """
    if not marker_template:
        marker_template = 'default_popup.html'
            
    marker_data = {"markers":[]}
    marker_data["zoomToFit"] = False # can/t zoom if there are no markers.
    marker_data["cluster"] = True
        
    if map_data and isinstance(map_data,(list,dict,)):
        if not isinstance(map_data,list):
            map_data = [map_data]
            
        for point in map_data:
            marker = {}
            marker["draggable"] = point.get('draggable',False)
            marker['map_icon'] = point.get('map_icon')
            marker['lat'] = point.get('lat')
            marker['lng'] = point.get('lng')
            marker['UID'] = point.get('UID')
            marker['title'] = point.get('title')
            marker['location_name'] = point.get('location_name')
            # for getting lat and lng values interactively from map
            marker['latitudeFieldId'] = point.get('latitudeFieldId')
            marker['longitudeFieldId'] = point.get('longitudeFieldId')
            
            if (marker['lat'] and marker['lng']) or (marker['latitudeFieldId'] and marker['longitudeFieldId']):
                marker_data['markers'].append(marker)
                # don't zoom in too close if only one point.
                if len(marker_data['markers']) > 1:
                    marker_data['zoomToFit'] = True
                    marker_data['zoom'] = None
                else:
                    marker_data['zoomToFit'] = False
                    marker_data['zoom'] = 16
                    
                popup = render_template(marker_template, point=point,**kwargs)
                popup = escapeTemplateForJson(popup)
                marker['popup'] = popup
    
    return render_template('simple_map.html',marker_data=marker_data,target_id=target_id)
    
    
@mod.route('/time_lapse', methods=['GET'])
@mod.route('/time_lapse/', methods=['GET'])
def time_lapse_map():
    """
    Display an automated map of bike sightings over time
    
    @@@ This is left over from the JumpStat maps but it might be a place to start in the future...
    
    """
    setExits()
    days = 1
    start_date = local_datetime_now() + timedelta(days=-1) # Always starts at midnight, yesterday
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=days,seconds=-1) 
    
    frame_duration = 10 * 60 # this many seconds of real time elapse between each frame
    seconds_per_frame = 1 # display each frame for this many seconds
        
    sql = """select id, lng, lat, sighted, retrieved from sighting where 
            retrieved >= '{start_date}' and sighted <= '{end_date}' 
            order by sighted
        """.format(start_date=start_date.isoformat(sep=' '), end_date=end_date.isoformat(sep=' '))
        
    recs = g.db.execute(sql).fetchall()

    marker_data = {"markers":[]}
    marker_data["zoomToFit"] = False # can/t zoom if there are no markers.
    
    if recs:
        """
        The Marker is a list of lists containing:
            lng,
            lat,
            display start seconds,
            display end seconds
        
        At play time in javascript, every frame_duration seconds loop through Markers:
            if display start seconds <= frame start time and display end seconds >= frame end time,
                set the marker opacity to 1
            else
                set opacity to 0
        """
        
        total_seconds = int(round((end_date - start_date).total_seconds(),0))
        marker_data["zoomToFit"] = True
        marker_data['total_seconds'] = total_seconds
        marker_data['frame_duration'] = frame_duration
        marker_data['seconds_per_frame'] = seconds_per_frame
        
        #import pdb;pdb.set_trace()
        for rec in recs:
            sighted_dt = getDatetimeFromString(rec['sighted'])
            if sighted_dt.day == 17:
                #import pdb;pdb.set_trace()
                pass
            #print('sighted_dt: {}'.format(sighted_dt))
            retrieved_dt = getDatetimeFromString(rec['retrieved'])
            #print('retrieved_dt: {}'.format(retrieved_dt))
            marker_data["markers"].append([round(rec['lng'],5),
                                        round(rec['lat'],5),
                                        int(round((sighted_dt - start_date).total_seconds(),0)),
                                        int(round((retrieved_dt - start_date).total_seconds(),0)),
                                    ])
                                
    return render_template('JSONmap.html', marker_data=marker_data,start_date=start_date)


@mod.route('/report/map_error', methods=['GET'])
@mod.route('/report/map_error/', methods=['GET'])
@mod.route('/report/map_error/<error_message>/', methods=['GET'])
def map_error(error_message=""):
    setExits()
    return render_template('map_error.html', error_message=error_message)
    
    
def escapeTemplateForJson(popup):
    # json doesn't like some characters rendered from the template
    if type(popup) != str and type(popup) != unicode:
        popup = ''
    popup = popup.replace('"','\\"') # to escape double quotes in html
    popup = popup.replace('\r',' ') # replace any carriage returns with space
    popup = popup.replace('\n',' ') # replace any new lines with space
    popup = popup.replace('\t',' ') # replace any tabs with space
    
    return popup
    

def getDivIcon(markerCount):
    """
    return an HTML block to be used as the DivIcon for a marker
    """
    if not markerCount:
        markerCount = "n/a"
    markerName = "BikeMarker_Blue.png"

    if type(markerCount) is int:
        if markerCount > 19:
            markerName = "BikeMarker_Green.png"
        if markerCount > 99:
            markerName = "BikeMarker_Gold.png"
        if markerCount > 199:
            markerName = "BikeMarker_Red.png"
            
    divIcon = render_template("map/divIcon.html", markerName=markerName, markerCount=markerCount)
    
    return escapeTemplateForJson(divIcon)
    

    
    