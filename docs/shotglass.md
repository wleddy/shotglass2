## shotglass.py

This module provides a number of basic services for the site.

---
> #### get_site_config(*this_app=None*): => app.config

Returns a copy of the current app.config.
This makes it possible for other modules to get access to the config
with the values as updated for the current host.
Import this method rather than importing app

When called from app.py, the app is passed in. When
called from other modules it is not needed.
  
---
> #### initalize_user_tables(*db*): => Nothing

Initialize the Users, Prefs and Roles tables

---
> #### make_db_path(*filespec*): => Boolean

Test the filespec path and if not found, create the path
but not the file.

Returns True if a new path was created, else False

---
> #### page_not_found(*error*): => Response

Handle 404 errors. If app.config REPORT_404_ERRORS is True, email alert to admin.

---
> #### register_users(*app*): => Nothing

Register the users blueprint

---
> #### register_www(*app*): => Nothing

Register the www blueprint

---
> #### server_error(*error*): => Response

Handle 500 errors. Email alert to admin.

 ---
> #### set_template_dirs(*this_app*): => Nothing

Compile a list of potential paths to search for
template files.

sets the global `g.template_list` with the search paths and
sets app.jinja_loader which flask will use when searching

Neither g.template_list nor app.jinja_loader will contain paths
to the blueprint template directories. Flask handles that after
the initial search so this works the same way.

---
> #### static(*filename*): => Response

Handle the lookup and delivery of a static file. Return the first matching file using paths:

1. app.config LOCAL_STATIC_DIRS
2. app.config STATIC_DIRS
3. static_folder value (if defined) of each blueprint in the order registered
4. finally, root static and shotglass2/static directories

---
> #### set_user_menus(): => Nothing

Add to or create `g.admin` global with the admin privileges for the User, Roles and Prefs tables.


---
[Return to Docs](/docs/shotglass2/README.md)


   
    