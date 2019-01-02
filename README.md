# Shotglass

This is designed as a starter Flask installation with a minimum of dependancies. Shotglass provides a very simple framework to start a Flask project.

By default, the main program file is app.py. App.py expects there to be two python packages called 'takeabeltof' and 'users' and out-of-the-box 
won't run without it.

The ['takeabeltof'](https://github.com/wleddy/takeabeltof) package is at github. All of the database functionality (sqlite3) is in this package so the first thing
you probably want to do is clone takeabeltof into your new flask app. If you're viewing this from a Shotglass site you can get the 
[README.md](/docs/takeabeltof/README.md) here.

The ['users'](https://github.com/wleddy/users) package is it's own repository on github as well. This gives you basic users and
 roles functionality as well as a prefs table.

## Hosting Multiple sites from one Installation

Shotglass has the ability to host multiple domains from the same server installation. [Read the details here](/docs/shared_domain_hosting.md).

## Overriding Static Content

It's possible to override the files in the default 'static' folder by creating your own versions in a folder outside of the shotglass
repo. [Read the instructions here](/docs/takeabeltof/docs/content_override.md).

## Instructions 

A typical approach to setting up a new development project would be to:

* create a new empty github repo for your new project
* clone it into your development machine
* get the .zip of the shotglass repo (don't clone it. You're making a new project)
* copy the contents of the .zip into your new project directory
* cd into the directory and clone the 'takeabeltof' & 'users' repos into it.
* ensure that .gitignore includes "/users" and "/takeabeltof"
* do an initial commit of your new project, but be sure NOT to include users
* in the terminal run `. setup_env` This will create the instance directory where your private
  stuff is stored and a 'resource' directory where you can put static content unique to the installation.  
  It will also try to create virtualenv directory 'env' and pip the requirements into it.  
  * See the note below about virtualenv and requirements.txt with A2 Hosting. 
* Assuming everything went Ok, run `. activate_env` to enter your virtual environment.
* Next, edit the file at `instance/site_settings.py` with all your secrets.
* run python app.py to start the dev server and create the initial database. (unless your on A2, see below)
    
## Special Instructions for A2 Hosting

A2 Hosting uses this `passenger` system to run python apps on their system. Read [special instruction here](/docs/passenger_setup.md).


### Required packages:

* python 3.6
* Flask and it's default dependencies, of course
* Flask-mail
* mistuse for Markdown support
* pytest

