# Upgrade Python Version for A2

This document describes how to install a new python site or new version of an existing site where a new version of Python is required.

## Decide on the location

Before you begin, decide on the home directory for your new version. You don't need to create it yet. We'll do that later.

For this example I'm going to assume the final app directory will be `~/Sites/williesworkshop.net/events3`

#### Note:

Save yourself some confusion if you are creating a new site. 
Plan on making the root directory match the domain name, then cread a new path for it as `Sites/mynewdomain.com/app_directory/` otherwise, the Python Setup app may not create your `.htaccess` file for you. If for some reason that happens, copy the conntents of another one, create the file in your root dir and update the contents as needed to point to your root and virtual environment.

## Load your app files

The first thing to do is install your application files. Use Terminal to ssh into the remote server. At this point we will be creating the directory that will be our web root.

1. `cd` into the directory that is one level above the final web root. e.g. `... williesworkshop.net`.
2. Clone the repo into a new directory with the web root name. In this example the command will be `git clone https://github.com/wleddy/staffing.git events3`.
3. Install any needed files from the previous version of the site such as the data or settings files.
4. For testing, update the `instance/site_settings.py` file to include host settings for the testing domain.

## Setup your domain for testing

Use the Control Panel to create a domain for testing the app. Set the Web Root to the Applicaiton Root used in the Python setup.

If you already have a domain setup for testing you can just change the Web Root to point to the new app location instead of creating a new domain.

## Setup the Python virtual environment

1. Create a Python App.
    a. Open Create Python app in Control Panel.
    b. Select the python version for your app.
    c. Set the "Application Root" to the home directory of the new version of the web site.
    d. For the "Application URL" select the new domain from the list and be sure to add the target directory in the text box to the right. In this case it will be `events3`.
    e. Leave "Application startup file" field empty.
    f. Leave "Application entry point" field empty.
    g. Set the "Passenger log file" to something like `logs/williesworkshop.net/events3.log`
    h. Click "Create" button.
    The setup progarm will create the virtual environment and the web root directory for the app.
    i. Copy the command in the new banner near the top of the form. You will use this to access the virtual environment. 
2. If things went well, a two files will be added at Applicaton Root you specified above. They should be:
   * `.htaccess` : This contains the Apache configuraion settings that tell Apache which virtual environment to load.
     * Edit this file to add the command `PassengerFriendlyErrorPages on` to get a better error page when setting up.
     * You will probobly want to comment this out in production.
   * `passenger_wsgi.py` : This is the python script that will be called whenever the site is accessed.
     * Initially it will just display "It Works!" in the browser. Later it will be edited to load app.py instead.
  
## pip in your requirements

1. Return to the Python App tool in Control Panel and click the editing icon. Copy the command at the top of the form.
2. Back at the terminal, paste the command to enter the virtual environment.
3. Install the required packages with `pip install -r requrements.txt`.

## Testing

If you created a new domain, there are no security certificate yet. This may take a day or so to be issued. You will not be able to access and test the site before this happens.

After the certificate has been issued, you can try the viewing the domain in a browser. It will simply display "It Works!"

Once that's working, edit the `'passenger_wsgi.py` file to simply contain one line:
    `from app import app as application`

You're now ready to test the app. You may need to run `touch tmp/restart.txt` in the remote terminal to get passenger to reload your app.

## Going live!

After everything checks out, update the home directory of the "Real" domain record to the new updated directory.
