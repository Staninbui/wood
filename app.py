import os
from flask import Flask, redirect, request, session, url_for, render_template
from ebaysdk.oauth2 import Connection

app = Flask(__name__)
# A secret key is needed for session management
app.secret_key = os.urandom(24)

# --- eBay API Configuration ---
# For local development, set these environment variables in your shell.
# On Cloud Run, set them as environment variables in the service configuration.
EBAY_APP_ID = os.getenv('EBAY_APP_ID')
EBAY_CERT_ID = os.getenv('EBAY_CERT_ID')
EBAY_RU_NAME = os.getenv('EBAY_RU_NAME')

# Define the required OAuth 2.0 scopes for the Feed API
SCOPES = ['https://api.ebay.com/oauth/api_scope/sell.feed.readonly']

@app.route('/')
def index():
    if 'ebay_token' in session:
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/login')
def login():
    if not all([EBAY_APP_ID, EBAY_CERT_ID, EBAY_RU_NAME]):
        return "Missing eBay API credentials in environment variables.", 500

    api = Connection(
        appid=EBAY_APP_ID,
        certid=EBAY_CERT_ID,
        ru_name=EBAY_RU_NAME,
        domain='api.ebay.com',
        config_file=None, # Do not use a yaml file
        https_required=True
    )
    auth_url = api.generate_authorization_url(SCOPES)
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    if not auth_code:
        return "Authorization code not found.", 400

    api = Connection(
        appid=EBAY_APP_ID,
        certid=EBAY_CERT_ID,
        ru_name=EBAY_RU_NAME,
        domain='api.ebay.com',
        config_file=None,
        https_required=True
    )

    try:
        # Exchange the authorization code for an access token
        api.get_access_token(auth_code)
        # The SDK stores the token internally, we can access it
        # For this app, we'll store the full token dictionary in the session
        session['ebay_token'] = {
            'access_token': api.credentials.access_token,
            'refresh_token': api.credentials.refresh_token,
            'token_expiry': api.credentials.token_expiry
        }
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error getting access token: {e}", 500

@app.route('/logout')
def logout():
    session.pop('ebay_token', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure the callback URL is correctly set for local testing
    print("--- Local Development Server ---")
    print(f"Ensure your eBay app's Redirect URI is set to: http://127.0.0.1:8080{url_for('callback')}")
    print("--------------------------------")
    app.run(debug=True, host='0.0.0.0', port=8080)
