## Template Loading

Shotglass2 uses a customizable template loading order. Two setting values control this:
1. HOST_TEMPLATE_DIRS
2. TEMPLATE_DIRS

Flask will search for templates in the order described below and use the first template it finds that matches the path.

This give you the ability to modify the templates for all hosts in the installation or selectively for each host. Copy the
templates from Shotglass2 or it's packages into your local directories and modify them as you wish.

#### HOST_TEMPLATE_DIRS:

This is a list of the relative paths that should be searched first. By default it's `['resource',]`. 

Not only will paths here be included in the search list, each value in this list will be prepended to each value in TEMPLATE_DIRS 
described below.

#### TEMPLATE_DIRS:

This list of relative paths to search is used after HOST_TEMPLATE_DIRS has failed to make a match.

#### The default search:

Finally the default Flask search is done.
1. The root 'templates' directory.
2. The 'template_folder' for each blueprint in the order the blueprints where registered on the app.


### Putting it all together...

Given:
* HOST_TEMPLATE_DIRS = ['resource/myhostname','resouce',]
* TEMPLATE_DIRS = ['templates/www','templates/user',]

The following searches will be done for a template file:

    resource/myhostname
    resource/myhostname/templates/www
    resource/myhostname/templates/user
    resource/
    resource/templates/www
    resource/templates/user
    templates/www
    templates/user
    templates
    { each of the blueprint template folders }

If you need to override some templates for a specific host within a shared installation, you can include a list value for "host_template_dirs" in
your SHARED_HOST_SETTINGS dictionary. [Read more about SHARED_HOST_SETTINGS here.](/docs/shared_domain_hosting.md)

If templates aren't loading the way you expect, enable the EXPLAIN_TEMPLATE_LOADING variable in site_settings. It will print out 
information about where it searched and what it found.

[Back to Docs](/docs/shotglass2/README.md)

