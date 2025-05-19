from flask import Flask, request, jsonify, render_template_string
from recommender import SmartTransportRecommender
import os

app = Flask(__name__)
recommender = None

# Initialize the recommender lazily to avoid startup errors
def get_recommender():
    global recommender
    if recommender is None:
        try:
            # Get current directory for relative paths
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bus_path = os.path.join(current_dir, 'bus.csv')
            train_path = os.path.join(current_dir, 'train.csv')
            flight_path = os.path.join(current_dir, 'flight.csv')
            
            recommender = SmartTransportRecommender(
                bus_path=bus_path,
                train_path=train_path,
                flight_path=flight_path
            )
            print("Recommender initialized successfully")
        except Exception as e:
            print(f"Error initializing recommender: {e}")
            # Create with default (sample) data
            recommender = SmartTransportRecommender()
    return recommender

@app.route('/')
def home():
    """Simple home page with API documentation"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Travel API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #2E7D32; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Smart Travel API</h1>
        <p>Available endpoints:</p>
        <ul>
            <li><code>GET /cities</code> - Get all available cities</li>
            <li><code>POST /recommend</code> - Get travel recommendations</li>
            <li><code>POST /predict_price</code> - Get price prediction for a specific mode</li>
        </ul>
        <h2>Example Usage:</h2>
        <pre>
fetch('/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        source: 'Delhi',
        dest: 'Mumbai',
        duration: 5
    })
}).then(res => res.json()).then(console.log)
        </pre>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/cities', methods=['GET'])
def get_cities():
    """Get available cities endpoint"""
    try:
        return jsonify(get_recommender().get_cities())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recommend', methods=['POST'])
def recommend():
    """Get travel recommendations endpoint"""
    try:
        data = request.json
        source = data.get('source')
        dest = data.get('dest')
        date = data.get('date')  # Optional
        hour = data.get('hour')  # Optional
        
        if not source or not dest:
            return jsonify({"error": "Source and destination are required"}), 400
            
        results = get_recommender().recommend(source, dest, date=date, hour=hour)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict_price', methods=['POST'])
def predict_price():
    """Get price prediction endpoint"""
    try:
        data = request.json
        source = data.get('source')
        dest = data.get('dest')
        duration = float(data.get('duration', 1))
        mode = data.get('mode')
        
        if not all([source, dest, mode]):
            return jsonify({"error": "Source, destination and mode are required"}), 400
            
        price = get_recommender().predict_price(source, dest, duration, mode)
        return jsonify({'price': price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Travel Recommender API...")
    app.run(port=5000, debug=True)
