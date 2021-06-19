## How to setup and access a gmail or gSuite email account with oAuth

1. Create a new project (if needed) at https://console.developers.google.com/
2. Click "Configure Consent Screen", then choose "Internal" since we will be the only ones with access.
3. Complete the required Project Name and email address fields and continue
4. In Scopes section select the "openid" scope and save.
5. Click "Back to Dashboard"
6. In the dashboard under “Credentials”, select “Create credentials” near the top of the form.
7. Choose "OAuth Client ID"
8. For Application Type, choose "Desktop App"
9. The Client ID and Client Secret are displayed. Save for later. 
10. From ..../shotglass2/takeabeltof/mail/google_oAuth run `python3 gmail_oauth_tool.py`
11. Record the Refresh Token returned by the tool
12. Use the Client ID, Client Secret, and Refresh Token in the site_settings file to use the account.
    