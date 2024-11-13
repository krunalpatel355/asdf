# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random  # For demo dashboard data
from EnhancedETL import EnhancedETL

app = Flask(__name__)

class VES:
    def get_data(self):
        # Single category with 10 buttons
        return {
            "options": [f"Option {i}" for i in range(1, 11)]
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

@app.route('/get_initial_data', methods=['POST'])
def get_initial_data():
    ves = VES()
    return jsonify(ves.get_data())

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
        etl = EnhancedETL()
        results = etl.perform_search(data)
        
        if results["status"] == "success":
            return jsonify({
                "status": "success",
                "results": f"""
                    Search ID: {results['search_id']}<br>
                    Total Posts Found: {results['total_posts']}<br>
                    Subreddits: {', '.join(results['subreddits'])}<br>
                    Time Range: {results['time_range']['from']} to {results['time_range']['to']}
                """
            })
        else:
            return jsonify({
                "status": "error",
                "message": results["message"]
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)