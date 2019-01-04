# Special Instructions for A2 Hosting

A2 Hosting uses this `passenger` system to run python apps on their system. Use the following steps to install your app.

1. In the terminal, `git clone` the new app as the directory you want to use.
2. cd into the new directory and `git clone https://github.com/wleddy/takeabeltof.git`
2. cd into the new directory and `git clone https://github.com/wleddy/users.git`
3. run `. setup_env` to create the instance directory. It will not actually create a virtualenv.
4. Go to the "Setup Python App" cpanel and create a new app.  
    * set the "App Directory" to the directory you just cloned.
    * set the "App URI" to the URI visitors will use to access the site.
    * Click "Setup" to create your virtualenv. The path to the new is displayed there.
5. Back at the terminal in your new directory type `nano instance/activate_env` enter the following: 
 
    ```
    #!/bin/bash

    echo 'activating env from instance'
    source /home/< your account name >/virtualenv/< path to your project >/<version>/bin/activate
    ```

6. Save it, exit and type `. activate_env` to enter the virtualenv.
7. Type `pip install -r requirements.txt`
8. Edit instance/site_settings.py to add all your secrets.
9. Edit the file `passenger_wsgi.py`. Delete all the default text and replace it with:

    `from app import app as application`
    
10. From the terminal, run `python app.py` This will start the development web server but also creates the default 
database records and is a good way to check that 
everything is working. If all goes well, type control + c to quit the dev server.
11. Type `touch tmp/restart.txt` to restart the app. You need to do this every time you make a change to the app.
13. In the App URI directory, A2 creates a default robots.txt file. Delete that to use the system at `www.views.home.robots`

***Easy as 1-2-3*** plus 10


## How to manually configure passenger setup

As of today, Nov. 27, 2018, this is what I think you need to do to manually fix/adjust/create the python settings 
for a site hosted on A2 Hosting

To begin with, setup the virtual environment using the  "Python Setup" cpanel. This will usually do everything needed to get you going, 
but the problem I have is that the cpanel does not show all of my environments so I could not make the changes I needed to make.

Below are the places to look for the bits to change the virtual environment and the python app settings that the server
will be looking for. Since I have no real idea what is going on under the hood this what I figured out by trial and error
as so it may not work in all cases

__Create .htaccess file__: if there is not one already, you need to create an file named `.htaccess` in the **document root** 
directory of your site. The file should contain something like this:

```
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "/home/leddysle/Sites/lindcraft/lindcraft2"
PassengerBaseURI "/"
PassengerPython "/home/leddysle/virtualenv/Sites_lindcraft_lindcraft2/3.6/bin/python3.6"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END

```

The "PassengerAppRoot" is the path to your python app. "PassengerPython" is the path to the virtual environment to use with
the app.

You can use the same `.htaccess` file in multiple doc roots if for some reason you want that.

My guess is that when a visitor hits the site, the Passenger... directives cause the web server to pipe the request to the 
python app indicated. That's just a guess...

[Back to Docs](/docs/shotglass2/README.md)
