# Hosting Multiple sites from one installation

Shotglass has the ability to host multiple domains from the same server installation. Each domain may have it's own database, static
files and templates or they may share those with base installation.

The magic happens in the `instance/site_settings.py` file. If that file contains a list variable named `SUB_DOMAIN_SETTINGS` it will
be used to override the default app.config values. The setting looks like this:
```
SUB_DOMAIN_SETTINGS = [
    {"host_name": HOST_NAME, "database_path": DATABASE_PATH,  
       "time_zone": TIME_ZONE, "local_static_dirs": LOCAL_STATIC_DIRS,  
       "contact_email_addr": CONTACT_EMAIL_ADDR, "contact_name": CONTACT_NAME},
    {"host_name": 'sf.jumpstat.williesworkshop.net', "database_path": 'instance/sf/sf_data.sqlite',  
        "time_zone": TIME_ZONE, "local_static_dirs": ("/resource/localhost/static"),},
    {"host_name": "sac.jumpstat.williesworkshop.net", "database_path": 'instance/sac/sac_data.sqlite',  
         "time_zone": TIME_ZONE, "local_static_dirs": ("/resource/sac/static"),},
    ]
```
`SUB_DOMAIN_SETTINGS` must be a list of dictionaries containing the names and values of any config values you want to override (or create).
Any values you don't supply will use the default values from `site_settings.py`. The key 'host_name' is tested against `flask.request.host` 
to determine the settings to use. If the host name is not found or if `SUB_DOMAIN_SETTINGS` does not exist, the base settings are
used.

----------------    
> ***IMPORTANT, use get_app_config()! *** You should not import app directly if you need to access to the site specific settings. If you do you'll get the
> default settings. Instead import `get_app_config` and call `get_app_config()`. It returns a reference to app.config with the 
> values for the current host. Then you can use them as `get_app_config()['SOME_SETTING']`.

----------------

For more information about customizing options see [content_override.md](/docs/content_override.md)

[Back to Docs](/docs/shotglass2/README.md)
