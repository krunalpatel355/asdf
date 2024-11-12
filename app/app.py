# app.py
from flask import Flask, render_template, request, jsonify
from VES.ves import VES
app = Flask(__name__)

# class VES:
#     def __init__(self):
#         # Simplified data structure without categories
#         self.data = ["item1", "item2", "item3", "item4", "item5", "item6", "item7", "item8", "item9"]
    
#     def process(self, input_text):
#         # In real implementation, process the input text
#         return {"items": self.data}

class ETL:
    def process(self, selected_items, advanced_params=None):
        # Sample implementation
        results = {
            "results": [f"Processed result for {item}" for item in selected_items]
        }
        
        if advanced_params:
            # Process advanced parameters
            search_box1 = advanced_params.get('search_box1', '')
            search_box2 = advanced_params.get('search_box2', '')
            option = advanced_params.get('option', '')
            results["advanced_results"] = [
                f"Advanced processing: {search_box1}, {search_box2}, {option}"
            ]
            
        return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_ves', methods=['POST'])
def process_ves():
    input_text = request.json.get('input_text', '')
    
    result = VES(input_text)
    return jsonify(result)

@app.route('/process_etl', methods=['POST'])
def process_etl():
    data = request.json
    selected_items = data.get('selected_items', [])
    advanced_params = data.get('advanced_params', None)
    etl = ETL()
    result = etl.process(selected_items, advanced_params)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)