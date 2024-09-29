from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sqlite3
import requests
import stripe

app = Flask(__name__)
# Apply CORS to the app
CORS(app)

app.secret_key = 'your_secret_key'  # Used for session encryption
api_key = "aW5mb0BxdWFudHVtcmVhY2htYXJrZXRpbmcuY29tOjZhYWRhODIzYjczNjljZmE="

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            credits = user[3]  # Assuming credits is the 4th column
            session['credits'] = credits
            session['username'] = username
            if credits < 2:
                # Logged-in user, render the full home page
                session['is_guest'] = True
                return render_template('home.html', error="Credits are used or use as a guest")         
            else:
                # Assume user authentication happens here
                session['username'] = username
                session['is_guest'] = False       
                return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('credits', None)  # Clear credits on logout
    session.pop('is_guest', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'username' in session:
        # Logged-in user, render the full home page
        return render_template('home.html', is_guest=False)
    elif session['guest']:      
        print("inside home route ;guest set to 0")
        session['credits'] = 0  # Ensure credits are 0 for guest users
        # Guest user, render the home page with masking
        return render_template('home.html', is_guest=True)    
    else:
        # If neither logged in nor guest, redirect to login
        return redirect(url_for('login'))

# Local Finder route (only accessible if logged in)
@app.route('/monthly_traffic', methods=['GET', 'POST'])
def monthly_traffic():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    if request.method == 'POST':
        try:
            # Handle POST request with JSON payload
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing request body'}), 400

            keyword = data.get('keyword')
          #  region = data.get('region')  # Get region from the payload
            print(keyword)
            if not keyword:
                return jsonify({'error': 'Keyword is required'}), 400
            
           # if not region:
            #    return jsonify({'error': 'Region is required'}), 400

            url = "https://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live"
            payload = [{
            "location_name":"United States",
            "language_name":"English",
            "bid":999,
        "match":"exact",
        "keywords":[
                keyword
                 ]
            }]
            headers = {
                    'Authorization': 'Basic aW5mb0BxdWFudHVtcmVhY2htYXJrZXRpbmcuY29tOjZhYWRhODIzYjczNjljZmE=',
                    'Content-Type': 'application/json'
            }


            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            if response.status_code != 200:
                return jsonify({'error': 'Error fetching data'}), 500

            return jsonify(data)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Render the Monthly Traffic page for GET request
    return render_template('monthly_traffic.html')

# Local Finder route (only accessible if logged in)
@app.route('/local_finder', methods=['GET', 'POST'])
def local_finder():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    if request.method == 'POST':
        try:
            # Handle POST request with JSON payload
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing request body'}), 400

            keyword = data.get('keyword')
            region = data.get('region')  # Get region from the payload
            
            if not keyword:
                return jsonify({'error': 'Keyword is required'}), 400
            
            if not region:
                return jsonify({'error': 'Region is required'}), 400

            # Pass the region to the payload
            url = "https://api.dataforseo.com/v3/serp/google/local_finder/live/advanced"
            payload = [{

                "language_code": "en",
                "location_code": region,
                "keyword": keyword,
                "min_rating": 4.5,
                "time_filter": "monday"
            }]

            headers = {
                'Authorization': 'Basic aW5mb0BxdWFudHVtcmVhY2htYXJrZXRpbmcuY29tOjZhYWRhODIzYjczNjljZmE=',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=payload, headers=headers)
            data = response.json()

            if response.status_code != 200:
                return jsonify({'error': 'Error fetching data'}), 500

            return jsonify(data)

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Render the Monthly Traffic page for GET request
    return render_template('local_finder.html')

# GET method to render HTML and fetch keyword metrics
@app.route('/get_keyword_metrics', methods=['GET'])
def get_keyword_metrics():
    # Check if user is logged in or a guest
    is_logged_in = 'username' in session
    is_guest = session.get('guest', False) and not is_logged_in  # Ensure guest is False if logged in

    if not is_logged_in and not is_guest:
        # Redirect to login if neither authenticated nor guest
        return redirect(url_for('login'))

    # Handle the GET request and fetch keyword metrics
    keywords_count = request.args.get('keywords_count')
    query = request.args.get('query')
    country_code = request.args.get('country_code')


    if not keywords_count or not query or not country_code:
        return render_template('get_keyword_metrics.html', error="All fields are required", result=None)

    try:
        # API request to get keyword metrics
        url = "https://bulk-keyword-metrics.p.rapidapi.com/seo-tools/get-bulk-keyword-metrics"
        querystring = {"keywords_count": keywords_count, "query": query, "countryCode": country_code}
        headers = {
            "x-rapidapi-key": "f99e7fdc91msh6674e4ecaa9e90cp180bf5jsn3f76ebe3fa53",  # Replace with your actual key
            "x-rapidapi-host": "bulk-keyword-metrics.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        response_data = response.json()

        if response.status_code != 200 or not response_data.get('success'):
            return render_template('get_keyword_metrics.html', error="Error fetching data from API", result=None)

        # Reduce 2 credits after successful API call
        user_id = session.get('username')
        if user_id:
            perform_action(user_id)

        # Mask data if the user is a guest
        if is_guest:
            for item in response_data['result']:
              #  item['CostPerClick'] = "Login to view"
                item['SeoDifficulty'] = "Login to view"

        return render_template('get_keyword_metrics.html', error=None, result=response_data['result'])
                
    except Exception as e:
        return render_template('get_keyword_metrics.html', error=f"An error occurred: {str(e)}", result=None)

@app.route('/get_keyword_suggestions', methods=['GET'])
def get_keyword_suggestions():

    # Check if user is logged in or a guest
    is_logged_in = 'username' in session
    is_guest = session.get('guest', False) and not is_logged_in  # Ensure guest is False if logged in

    if not is_logged_in and not is_guest:
        # Redirect to login if neither authenticated nor guest
        return redirect(url_for('login'))

    keyword = request.args.get('keyword')
    country = request.args.get('country_code')

    if not keyword or not country:
        return render_template('get_keyword_suggestions.html', error="All fields are required", result=None)

    try:
        url = "https://seo-keyword-research.p.rapidapi.com/keynew.php"
        querystring = {"keyword": keyword, "country": country}
        headers = {
            "x-rapidapi-key": "f99e7fdc91msh6674e4ecaa9e90cp180bf5jsn3f76ebe3fa53",  # Replace with your actual key
            "x-rapidapi-host": "seo-keyword-research.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        response_data = response.json()

        if response.status_code != 200 or not isinstance(response_data, list):
            return render_template('get_keyword_suggestions.html', error="Error fetching data from API", result=None)

        # Reduce 2 credits after successful API call        
        user_id = session.get('username')
        if user_id:
            perform_action(user_id)
            
        # Mask data if the user is a guest
        if is_guest:
            for item in response_data:
                item['cpc'] = "Login to view"
               # item['competition'] = "Login to view"
                item['score'] = "Login to view"

        return render_template('get_keyword_suggestions.html', error=None, result=response_data[:20])

    except Exception as e:
        return render_template('get_keyword_suggestions.html', error=f"An error occurred: {str(e)}", result=None)


@app.route('/guest_access')
def guest_access():
    session['guest'] = True  # Mark the session as a guest
    return redirect(url_for('home'))  # Redirect to the home route

    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        # Create a new user with default credits = 10
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, credits) VALUES (?, ?, ?)", (username, password, 10))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


# Configure Stripe with your API keys
stripe.api_key = "sk_test_hZiY4T7noF63WJblAp1PmZPb"

@app.route('/buy_credits', methods=['GET', 'POST'])
def buy_credits():
    if request.method == 'POST':
        try:
            # Parse JSON request body
            data = request.get_json()  
            payment_method_id = data.get('payment_method_id')
            firstname = data.get('first_name')
            lastname = data.get('last_name')
            address = data.get('address')
            if not payment_method_id:
                return jsonify({'error': 'Payment method ID not found'}), 400

            # Create a payment intent
            amount = 500  # 5 dollars in cents
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # This prevents redirect-based payment methods
                }
            )

            # Add credits to user's account
            user_id = session.get('username')
            print(user_id)
            print(firstname)
            print(lastname)
            print(address)
            savecred_user(user_id, 25,firstname,lastname,address)  # Save updated user data (Add credits)

            return jsonify({'success': True}), 200  # Respond with success
        except stripe.error.CardError as e:
            return jsonify({'error': 'Your card was declined'}), 400

    # For GET request, render the buy_credits.html template
    return render_template('buy_credits.html')

def get_user_by_id(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def save_user(user_id, credits):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET credits = ? WHERE username = ?", (credits, user_id))
    conn.commit()
    conn.close()
    session['credits'] = credits

def savecred_user(user_id, credits, first_name, last_name, address):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    session['credits'] = credits
    # Update user data
    update_query = "UPDATE users SET credits = ?, "
    update_params = [credits]

    if first_name is not None:
        update_query += "first_name = ?, "
        update_params.append(first_name)

    if last_name is not None:
        update_query += "last_name = ?, "
        update_params.append(last_name)

    if address is not None:
        update_query += "address = ?, "
        update_params.append(address)

    update_query = update_query[:-2] + " WHERE username = ?"
    update_params.append(user_id)

    try:
        c.execute(update_query, update_params)
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error updating user: {e}")
    finally:
        conn.close()

def perform_action(user_id):
    user = get_user_by_id(user_id)
    if user and user[3] >= 2:  # Checking if user has enough credits
        credits = user[3] - 2  # Deduct 2 credits
        save_user(user_id, credits)
        # Perform the action here
        return "Action performed"
    else:
        return "Not enough credits"

# API Route for domain info
@app.route('/get_domain_info', methods=['GET'])
def get_domain_info():

  # Check if user is logged in or a guest
    is_logged_in = 'username' in session
    is_guest = session.get('guest', False) and not is_logged_in  # Ensure guest is False if logged in

    if not is_logged_in and not is_guest:
        # Redirect to login if neither authenticated nor guest
        return redirect(url_for('login'))

    domain = request.args.get('domain')

    if not domain:
        return render_template('get_domain_info.html', error="Please enter a domain.", result=None)

    try:
        # Make the API request
        url = "https://domain-authority1.p.rapidapi.com/seo-tools/get-domain-info"
        querystring = {"domain": domain}
        headers = {
            "x-rapidapi-key": "f99e7fdc91msh6674e4ecaa9e90cp180bf5jsn3f76ebe3fa53",  # Replace with your actual key
            "x-rapidapi-host": "domain-authority1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response_data = response.json()

        # Check if the response contains the required data
        if response.status_code != 200 or 'result' not in response_data:
            return render_template('get_domain_info.html', error="Error fetching data from API", result=None,is_guest=is_guest,is_logged_in=is_logged_in)

        # Extract domain metrics
        result = response_data['result']

        # Reduce 2 credits after successful API call
        user_id = session.get('username')
        print(user_id)
        if user_id:
            perform_action(user_id)

        print(f"Session Data: {session}")

       # Mask data if the user is a guest
        if is_guest:
                print("guest...")
                result['average_rank'] = "Login to view"
                result['keywords_rank'] = "Login to view"

        return render_template('get_domain_info.html', error=None, result=result)

    except Exception as e:
        return render_template('get_domain_info.html', error=f"An error occurred: {str(e)}", result=None)

    
@app.route('/get_competitordomain_metrics', methods=['GET'])
def get_competitordomain_metrics():

    # Check if user is logged in or a guest
    is_logged_in = 'username' in session
    is_guest = session.get('guest', False) and not is_logged_in  # Ensure guest is False if logged in

    if not is_logged_in and not is_guest:
        # Redirect to login if neither authenticated nor guest
        return redirect(url_for('login'))

    domain = request.args.get('domain')

    if not domain:
        return render_template('get_competitordomain_metrics.html', error="Domain is required", result=None)

    try:
        # API call setup
        url = "https://seo-website-ranking-keywords.p.rapidapi.com/"
        querystring = {"domain": domain, "offset": "0", "order_by": "position", "sort_by": "desc"}
        headers = {
            "x-rapidapi-key": "f99e7fdc91msh6674e4ecaa9e90cp180bf5jsn3f76ebe3fa53",  # Your key here
            "x-rapidapi-host": "seo-website-ranking-keywords.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        response_data = response.json()
        print(response_data)
        # Handle valid API response
        if response.status_code == 200 and 'keywords' in response_data:
            keywords = response_data.get('keywords', [])
            # Reduce 2 credits after successful API call
            user_id = session.get('username')
            if user_id:
                perform_action(user_id)
            if not keywords:
                return render_template('get_competitordomain_metrics.html', error="No keywords found", result=None)

            # Filter and prepare keyword data
            filtered_keywords = [
                {
                    "keyword": kw.get("keyword"),
                    "rank":kw.get("rank"),
                    "url": kw.get("url"),
                    "title": kw.get("title"),
                    "avg_search_volume": kw.get("avg_search_volume"),
                    "competition_level": kw.get("competition_level"),
                    "keyword_difficulty": kw.get("keyword_difficulty")
                }
                for kw in keywords
            ]

            # Mask data for guest users
            if is_guest:
                for item in filtered_keywords:
                   # item['avg_search_volume'] = "Login to view"
                   # item['competition_level'] = "Login to view"
                    item['keyword_difficulty'] = "Login to view"

            return render_template('get_competitordomain_metrics.html', error=None, result=filtered_keywords, is_guest=is_guest, is_logged_in=is_logged_in)

        return render_template('get_competitordomain_metrics.html', error="Error fetching data from API", result=None)

    except Exception as e:
        return render_template('get_competitordomain_metrics.html', error=f"An error occurred: {str(e)}", result=None)



if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
