* Create gmail credentials

This is the procedure to create oAuth credentials for a gmail or gSuite email account that
can be used in the `shotglass2` email system.

1. Go to `https://console.developers.google.com` to set up your api and download your credentials.
    
    *** Also, it's very important that you ENABLE the api at the same time. ***
    
    For background details got to 
    `https://www.thepythoncode.com/article/use-gmail-api-in-python#Enabling_Gmail_API`
    
2. After you have downloaded the credentials file from the API dashboard/credentials page
   from the terminal run `fetch_auth_pickle.py` and follow the prompts.
   
This will walk through the process of creating a gmail oAuth credentials object
and store it in a pickle file.

Once you have the pickle file you can move it to the web server machine and point your
settings to it.

The files used by and created by `fetch_auth_pickle.py` contain confidential information and
should not be committed to the repo.

