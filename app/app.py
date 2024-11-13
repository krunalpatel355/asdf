# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random  # For demo dashboard data
from flask import jsonify, request
from datetime import datetime
from Enhanced_etl import EnhancedETL, SearchParameters
from VES.ves import VectorSrc

app = Flask(__name__)

class VES:
    def __init__(self,user_input):
        self.user_input = user_input
    def get_data(self):
        # Single category with 10 buttons
        results = VectorSrc(self.user_input)
        return {
            # "options": [f"Option {i}" for i in range(1, 11)]
            "options":results
        }

class SRC:
    def search(self, selected_buttons):
        return f"Results for buttons: {', '.join(selected_buttons)}"

class ETL:
    def search(self, selected_buttons, from_time, to_time, options, search_text):
        return f"Advanced search results for: {search_text} between {from_time} and {to_time}"

@app.route('/')
def index():
    return render_template('index.html', active_page='search')

@app.route('/dashboard')
def dashboard():
    # Generate some sample data for the dashboard
    monthly_data = [random.randint(1000, 5000) for _ in range(12)]
    performance_data = [random.randint(60, 100) for _ in range(6)]
    status_data = {
        "Active": random.randint(100, 200),
        "Pending": random.randint(20, 50),
        "Completed": random.randint(300, 400)
    }
    return render_template('dashboard.html', 
                         active_page='dashboard',
                         monthly_data=monthly_data,
                         performance_data=performance_data,
                         status_data=status_data)

from flask import request, jsonify

@app.route('/get_initial_data', methods=['POST'])
def get_initial_data():
    # Retrieve the JSON data from the request
    data = request.get_json()
    user_input = data.get('text')  # Get the 'text' value from JSON payload
    result_data = VectorSrc(user_input)
    # # Pass the user_input to your VES class or use it in your logic
    # ves = VES(user_input)
    # result_data = ves.get_data()  # Assume VES.get_data can accept input

    return jsonify(result_data)

@app.route('/simple_search', methods=['POST'])
def simple_search():
    selected_buttons = request.json.get('selected_buttons', [])
    src = SRC()
    results = src.search(selected_buttons)
    return jsonify({"results": results})

@app.route('/advanced_search', methods=['POST'])
def advanced_search():
    try:
        data = request.json
        
        # Create search parameters
        params = SearchParameters(
            topics=data['selected_buttons'],
            from_time=datetime.fromisoformat(data['from_time']),
            to_time=datetime.fromisoformat(data['to_time']),
            post_types=data['post_types'],  # ['hot', 'new', 'top']
            post_limit=int(data['post_limit']),
            include_comments=data['include_comments'] == 'yes',
            search_text=data.get('search_text')
        )
        
        # Initialize ETL with your credentials
        etl = EnhancedETL(
            mongodb_uri="your_mongodb_uri",
            reddit_credentials={
                "client_id": "your_client_id",
                "client_secret": "your_client_secret",
                "user_agent": "your_user_agent"
            }
        )
        
        # Perform search and get search ID
        search_id = etl.perform_search(params)
        
        # Get results
        results = etl.get_search_results(search_id)
        
        return jsonify({
            "success": True,
            "search_id": search_id,
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)