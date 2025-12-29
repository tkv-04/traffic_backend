from flask import Flask, render_template, jsonify, request
from traffic_processor import TrafficProcessor
import os
import json

app = Flask(__name__)

# Initialize Processor
# In a real scenario, we might load these from os.environ
CRED_PATH = os.environ.get('FIREBASE_CRED_PATH')
DB_URL = os.environ.get('FIREBASE_DB_URL')
processor = TrafficProcessor(cred_path=CRED_PATH, db_url=DB_URL)

# Sample data for demonstration if no Firebase connection
SAMPLE_DATA = """
{
  "01-08-2025": {
    "id1": {
      "status": "Wrong Parking",
      "vehicle_count": 12,
      "timestamp": 1754061400,
      "reason": "Illegal stop",
      "suggestion": "Clear area"
    },
    "id2": {
      "status": "Signal Delay",
      "vehicle_count": 8,
      "timestamp": 1754061500,
      "reason": "Light malfunction",
      "suggestion": "Fix light"
    },
    "id3": {
      "status": "Wrong Parking",
      "vehicle_count": 15,
      "timestamp": 1754061600,
      "reason": "Blocking lane",
      "suggestion": "Tow vehicle"
    },
    "id4": {
      "status": "Clear",
      "vehicle_count": 5,
      "timestamp": 1754061700,
      "reason": "Normal flow",
      "suggestion": "None"
    }
  }
}
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/traffic-data')
def get_traffic_data():
    # If we have firebase initialized, use it
    if processor.db_ref:
        try:
            raw_data = processor.get_data_from_firebase()
            data = processor.process_data(raw_data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        # Fallback to sample data for demo purposes
        # Or allow passing JSON via query param for testing?
        # Let's just use the hardcoded sample for a "demo mode"
        raw_data = processor.get_data_from_json(SAMPLE_DATA)
        data = processor.process_data(raw_data)
        
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
