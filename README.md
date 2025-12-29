# Traffic Analytics Dashboard

A Flask-based web application for real-time traffic congestion monitoring and analysis. Processes traffic data from Firebase and displays insights through an interactive dashboard.

## Features

- 📊 **Real-time Dashboard** - Vehicle counts, congestion sources, and traffic trends
- 🔥 **Firebase Integration** - Connects to Firebase Realtime Database for live data
- 📈 **Interactive Charts** - Line chart for traffic trends, pie chart for congestion breakdown
- 📋 **Action Reports** - Identified issues with recommended solutions

## Installation

```bash
# Clone the repository
git clone https://github.com/tkv-04/traffic_backend
cd code

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set environment variables for Firebase (optional):

```bash
set FIREBASE_CRED_PATH=path/to/your/firebase-credentials.json
set FIREBASE_DB_URL=https://your-project.firebaseio.com
```

If not configured, the app runs in demo mode with sample data.

## Usage

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## API Endpoint

### GET `/api/traffic-data`

Returns processed traffic data:

```json
{
  "vehicleCount": 15,
  "time": "3:30",
  "congestion": [
    { "name": "Wrong Parking", "percentage": 50 },
    { "name": "Signal Delay", "percentage": 33.3 }
  ],
  "report": [
    {
      "reason": "Wrong Parking (Illegal stop)",
      "suggestion": "Remove parked vehicles to restore traffic flow."
    }
  ],
  "graph": [
    {
      "timestamp": "8:46:02,01-08-2025",
      "percentage": 50,
      "reason": "Wrong Parking"
    }
  ]
}
```

## Project Structure

```
├── app.py                 # Flask application
├── traffic_processor.py   # Data processing logic
├── test_traffic.py        # Unit tests
├── requirements.txt       # Dependencies
└── templates/
    └── index.html         # Dashboard UI
```

## Input Data Format

Expected Firebase structure:

```json
{
  "01-08-2025": {
    "-pushId123": {
      "date": "01-08-2025",
      "status": "Wrong Parking",
      "reason": "Illegal stop",
      "suggestion": "Clear area",
      "vehicle_count": 12,
      "timestamp": 1754061400
    }
  }
}
```

## Testing

```bash
python -m pytest test_traffic.py
```

## License

MIT
