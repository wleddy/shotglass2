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
    `git clone https://github.com/wleddy/shotglass2.git`
* From the terminal run `cp -R shotglass2/a_starter_app/ . `
* Next run `. setup_env` This will create the instance directory where your private
  stuff is stored and a 'resource' directory where you can put static content unique to the installation.  
  It will also try to create virtualenv directory 'env' and pip the requirements into it.  
  * See the note below about virtualenv and requirements.txt with A2 Hosting. 
* If not already in the virtual environment, run `. activate_env` to enter your virtual environment.
* Next, edit the file at `instance/site_settings.py` with all your secrets.
* run python app.py to start the dev server and create the initial database. (unless your on A2, see below)
    
### Special Installation Instructions for A2 Hosting

A2 Hosting uses this `passenger` system to run python apps on their system. [Read more here](/docs/passenger_setup.md).

## Hosting Multiple sites from one Installation

Shotglass has the ability to host multiple domains from the same server installation. Each site may have it's own database, style
sheet and other content. The sites are configured in the application settings file.

[Get the details here](/docs/shared_domain_hosting.md).

## Overriding Static Content

It's possible to override the files in the default 'static' folder by creating your own versions in a folder outside of the shotglass
repo. [Read more here](/docs/takeabeltof/content_override.md).

## Database Access and Utility functions

Database access and some utility functions are grouped in the 'takeabeltof' package. [Read more here.](/docs/takeabeltof/index.md)

## The User, Role, and Pref tables

A basic users and roles functionality is provided in the 'users' package. [Read More Here.](/docs/users/index.md)

### Required packages:

* python 3.6
* Flask
* Flask-mail
* mistuse for Markdown support
* namedlist
* pytest
* pytz


