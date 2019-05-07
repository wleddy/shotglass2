/**
 * Generic Map Implementation
 *
 * @param mapboxProjectId
 * @param mapboxAccessToken
 * @param mapDivId
 * @constructor
 */
	
function Map(mapboxProjectId, mapboxAccessToken, mapDivId) {
	// create a layerGroup each for pushpin and canvas markers
	this.pushPinLayer = new L.LayerGroup();
	this.canvasLayer = new L.LayerGroup();
	initialZoom = 2;
    this.map = L.map(mapDivId, {
        center: [43.551253, -121.488683],
        zoom: initialZoom,
    });
	
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
        zoom: this.map.options.zoom,
        id: mapboxProjectId,
        accessToken: mapboxAccessToken
    }).addTo(this.map);

    if (L.markerClusterGroup !== undefined) {
        this.cluster = L.markerClusterGroup();
    }
	
    this.geocodes = [];
    this.locations = [];
	// Davis Bike Hall of Fame
	//var lng = -121.74439430236818;
	//var lat = 38.54422161206573;
    default_location = {'lat':38.54422161206573, 'lng':-121.74439430236818}
}

Map.prototype = {
    
    constructor: Map,
    
	/**
	Add markers using JSON object
	*
	* @param JSON object with all marker data
	* @param url of error response page
	*
	*/
    
	marker_data: {},
    //local_locations: [],
    
	addMarkersFromJSON: function(data,errorPage){
		var parseError =false;
		var errorMess = '';
		// var mapIcon = getJumpIcon();

		try{
			marker_data = JSON.parse(data);
            
		}catch(errorMess){
			alert("err '" + errorMess + "'");
			parseError = true;
		}
		if(!parseError){			
			for (var i = 0; i < marker_data.markers.length; i++) {
			    data = marker_data.markers[i]
                /*
                Each marker element is an array as:
                    lat,
                    lng,
                optional:
                    UID,
                    title,
                    popup
                */
				var options = {};
				var draggable = false;
				if (data.draggable != undefined){
					draggable = (data.draggable == true );
				}
				options.draggable = draggable;
                if (data.map_icon != undefined){options.icon = map_icon}
				
                if (data.lat == null || data.lng == null || data.lat == '' || data.lng == ''){
                    // get the current location and set this marker there...
                    if (navigator.geolocation) {
                        var self = this;
                        // set the defaults first
                        data.lat = default_location.lat;
                        data.lng = default_location.lng;

                        navigator.geolocation.getCurrentPosition(function(position) {
                            // getCurrentPosition only works over secure connections.
                            if (position != undefined){
                                // Add the location
                                data.lat = position.lat;
                                data.lng = position.lng;
                            } else {
                                console.log('Did not get the position from geoloaction');
                            }
                        })
                    } else {
                        console.log("Geolocation is not supported by this browser.");
                    }
                    
                }
                if (!this.mapHasMarkerAt(data.lat,data.lng)){
                    var marker = L.marker([data.lat, data.lng],options);
                
					this.pushNewLocation(data,marker)
                
					this.setDragFunction(marker);
					// Update the location fields is provided.
                
					popper = "Un-named Location"
					if (data.popup != undefined) {
						popper = data.popup;
					} else {
						if(data.title != undefined){
							popper = data.title;
						}
				
					} // bindPopup
					marker.bindPopup(popper);
                
                    /*
					if (data.divIcon != undefined){
						var divIcon = new L.DivIcon({
					        className: 'divIcon',
					        html: data.divIcon,
							iconAnchor: new L.Point(20, 80),
							popupAnchor: new L.Point(0, -80),
					    });
    					marker.options.icon = divIcon;
					}
                    */
                
                
					// Put the maker into the cluster layer if reqested
					if (marker_data.cluster === true) {
			            this.cluster.addLayer(marker);
			        } 
					// add the marker (layer) to the pushPinLayer LayerGroup
					this.pushPinLayer.addLayer(marker);
                }
					
			} // end for: all markers created
            this.pushPinLayer.addTo(this.map)
            
			if (marker_data.cluster === true) {
				this.pushPinLayer = this.cluster;
			}
			this.setZoomFunction(this.map,this.pushPinLayer,this.canvasLayer);
			//this.map.setZoom(initialZoom-1);
            

	        if (marker_data.zoomToFit != undefined && marker_data.zoomToFit == true) {
					this.zoomToFitAllMarkers();
	        //} else if (marker_data.zoom != undefined && marker_data.zoom >= 0 && marker_data.zoom <= 13 ) {
	        } else if (marker_data.zoom != undefined) {
                this.centerOnMarker(marker)
	            this.map.setZoom(marker_data.zoom,this.map.options);
	        }
            else {
	            // Show the whole world
				this.map.fitWorld();
	        }				
		}else{
			// error parsing JSON data
			// go to error page
			document.location = errorPage + errorMess + "/";
		}
		// end of addMarkersFromJSON()
	},
		
    /**
     * Push a new location to the locations array.
     * Also pushes the location lat/lon to the geocodes array (used to zoom map to markers).
     *
     * @param locationName
     * @param latitude
     * @param longitude
     * @param tripCount
     */
    pushNewLocation: function(data,marker) {
        this.geocodes.push([data.lat, data.lng]);
    },

	mapHasMarkerAt: function (lat,lng){
	    // Check if trip location already exists
	    for (var trip in this.locations) {
            if (this.locations.lat == lat && this.locations.lng == lng) {
                // if the location already exists return true
                return true;
	        }
	    }
		return false
	},
    
    animation: function(){
        marker_data.frame_start_time = marker_data.frame_end_time;
        marker_data.frame_end_time = marker_data.frame_end_time + marker_data.frame_duration;
        if (marker_data.frame_end_time > marker_data.total_seconds) {
            // go to the begining
            marker_data.frame_start_time = 0;
            marker_data.frame_end_time = marker_data.frame_duration;
        }
        //id="display_date"></span> <span id="display_time"
        the_time = marker_data.frame_start_time / 3600;
        if (the_time < 0){ the_time = 0;}
        hours = Math.trunc(the_time);
        minutes = Math.trunc((the_time - hours)*60);
        
        $('#display_time').text('Time: '+("00" + hours.toString()).substr(-2)+ ":" + ("00" + minutes.toString()).substr(-2))
        if (local_locations == undefined){
            local_locations = this.locations;
        }
            for (var y=0; y<local_locations.length; y++){
                // check every marker
                my_loc = local_locations[y]
                if (local_locations[y].starting_time_code <= marker_data.frame_start_time &&
                    local_locations[y].ending_time_code >= marker_data.frame_end_time                           
                    ) {
                        local_locations[y].marker.setOpacity(1);
                    } else {
                        local_locations[y].marker.setOpacity(0);
                    }
            }
    },

    /**
     * Zoom the map to fit the location markers.
     */
    zoomToFitAllMarkers: function() {
        var bounds = new L.LatLngBounds(this.geocodes);
		this.map.fitBounds(bounds);
    },
    
    centerOnMarker: function(marker) {
        if (marker != undefined){
          var latLngs = [ marker.getLatLng() ];
          var markerBounds = L.latLngBounds(latLngs);
          this.map.fitBounds(markerBounds);
        }
    },
	setDragFunction: function(theMarker){
		var self = this;
		// 'draggable' is in the 'options' object
        if (theMarker.options.draggable === true) {
            // Add drag event handler
            theMarker.on('dragend', function (event) {
                var marker = event.target;
                var position = marker.getLatLng();

                self.updateFormLocationFields("latitude", "longitude", position.lat, position.lng);
            });
		}
    },
	setZoomFunction: function(theMap,clusterLayer,canvasLayer){
		if(theMap != undefined){
			theMap.on("zoomend", function (event) {
				var theZoom = theMap.getZoom()
                /*
				if (theZoom > this.options.flowMarkerMinZoom) {
					clusterLayer.remove();
					canvasLayer.addTo(theMap);
				} else {
					canvasLayer.remove();
					clusterLayer.addTo(theMap);
				}
                */
			});
		}
	},

    /**
     * Update the location form input fields.
     *
     * @param latitudeFieldId
     * @param longitudeFieldId
     * @param latitude
     * @param longitude
     * @param NSheadingFieldID
     * @param EWheadingFieldID
     * @param NSheading
     * @param EWheading
     */

    updateFormLocationFields: function(latitudeFieldId, longitudeFieldId, latitude, longitude, NSheadingFieldID, EWheadingFieldID, NSheading, EWheading) {
        if (latitudeFieldId !== undefined && longitudeFieldId !== undefined) {
			var theID = document.getElementById(latitudeFieldId);
			if(theID != null){theID.value = latitude;}
			theID = document.getElementById(longitudeFieldId);
			if(theID != null){theID.value = longitude;}
			theID = document.getElementById(NSheadingFieldID);
			if(theID != null){theID.value = NSheading;}
			theID = document.getElementById(EWheadingFieldID);
			if(theID != null){theID.value = EWheading;}
        }
    }

};

