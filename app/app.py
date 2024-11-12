# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random  # For demo dashboard data

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
    data = request.json
    etl = ETL()
    results = etl.search(
        data.get('selected_buttons', []),
        data.get('from_time'),
        data.get('to_time'),
        {
            'option1': data.get('option1'),
            'option2': data.get('option2'),
            'option3': data.get('option3')
        },
        data.get('search_text')
    )
    return jsonify({"results": results})

if __name__ == '__main__':
    app.run(debug=True)