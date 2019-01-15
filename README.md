# Shotglass2

Shotglass2 is my second attempt at creating a simple web site starter kit using Python and the [Flask](http://flask.pocoo.org) "Micro Framework".

Out of the box it provides most of the basics for a web site including:

* A basic mobile responsive layout using the w3.css style sheet ([w3schools.com](https://www.w3schools.com/w3css/default.asp)).
* An Sqlite3 database with Users, Roles, and Prefs tables with access control.
* Optional user account signup with administrator confirmation.
* Basic Email functions for visitor contact etc.
* Documentation viewing system
* Markdown rendering of page content available.
* The option to host multiple sites from one installation.

## Installation 

A typical approach to setting up a new development project would be to:
* Create a new empty github repo for your new project
* Clone it into your development machine
* cd into the new directory and clone shotglass2 into it with:
    ```
    git clone https://github.com/wleddy/shotglass2.git
    ```
* From the terminal run:
    ```
    cp -r shotglass2/a_starter_app/. .
    ```
* Next run `. setup_env`  
  This will create the instance, resource and templates directories:
    * The 'instance' directory is where you'll keep your private info such as the encryption key and email account info. The database files
    are usually stored here too.
    * The 'resource' directory is a good place to put static content and/or templates unique to a particular host.
    [More info here.](/docs/content_override.md)
    * The 'template' directory is where your primary site design file go. You can copy templates from shotglass2/templates and
     edit them to suit your needs or add new ones.  
    
    * setup_env will also try to create virtualenv directory 'env' and pip the requirements into it.  
        * See the note below about virtualenv and requirements.txt with A2 Hosting.  
* You should now be in the virtual environment. If not, type `. activate_env` to activate it.
* Next, edit the file at `instance/site_settings.py` with all your secrets.
* Enter `python app.py` to start the dev server and create the initial database. (unless your on A2, see below)
    
### Special Installation Instructions for A2 Hosting

A2 Hosting uses this `passenger` system to run python apps on their system. [Read more here](/docs/passenger_setup.md).

## shotglass.py

shotglass.py handles a number of tasks that used to be part of app in the old shotglass setup. [Read more here.](/docs/shotglass.md)

## Template Loading Order

Shotglass2 uses a customizable template loading order. Two setting values control this:
1. HOST_TEMPLATE_DIRS
2. TEMPLATE_DIRS

[Read more here.](/docs/template_loading.md)

## Hosting Multiple sites from one Installation

Shotglass has the ability to host multiple domains from the same server installation. Each site may have it's own database, style
sheet and other content. The sites are configured in the application settings file.

[Get the details here](/docs/shared_domain_hosting.md).

## Overriding Static Content

It's possible to override the files in the default 'static' folder by creating your own versions in a folder outside of the shotglass
repo. [Read more here](/docs/content_override.md).

## Utility Functions and Database Access

Database access and some utility functions are grouped in the 'takeabeltof' package. [Read more here.](/docs/takeabeltof/index.md)

## The User, Role, and Pref tables

A basic users and roles functionality is provided in the 'users' package. [Read More Here.](/docs/users/index.md)

### Required packages:

* python 3.6
* Flask
* Flask-mail
* mistune for Markdown support
* namedlist
* pytest
* pytz


