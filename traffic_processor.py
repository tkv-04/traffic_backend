import json
from collections import Counter
from datetime import datetime

try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Warning: firebase_admin module not found. Only local JSON processing will work.")

class TrafficProcessor:
    def __init__(self, cred_path=None, db_url=None):
        self.db_ref = None
        if cred_path and db_url:
            if not FIREBASE_AVAILABLE:
                raise ImportError("firebase_admin not installed. Run: pip install firebase-admin")
            try:
                if not firebase_admin._apps:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {'databaseURL': db_url})
                self.db_ref = db.reference()
            except Exception as e:
                print(f"Warning: Failed to initialize Firebase: {e}")

    def get_data_from_firebase(self, path="/"):
        if not self.db_ref:
            raise ValueError("Firebase not initialized. Provide cred_path and db_url.")
        return self.db_ref.child(path).get()

    def get_data_from_json(self, json_str):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to fix common user input error where they use [] for dicts
            # This is a basic repair attempt for the specific sample pattern
            print(f"JSON Parse Error: {e}. Attempting loose parsing...")
            try:
                # Replace incorrect array brackets with dict braces if they look like dicts
                fixed_str = json_str.replace('": [', '": {').replace(']"', '}"')
                if fixed_str.strip().endswith(']'):
                    fixed_str = fixed_str.strip()[:-1] + '}'
                return json.loads(fixed_str)
            except:
                raise ValueError(f"Invalid JSON format: {e}")

    def process_data(self, data):
        """
        Processes raw Firebase data into the target API format.
        Expected Input Format: {"DATE": {"PUSH_ID": {...data...}}}
        """
        all_records = []
        
        # Normalize input to a flat list of records
        if isinstance(data, dict):
            for date_key, valid_data in data.items():
                if isinstance(valid_data, dict):
                    # Standard Firebase: {"id": {data}, "id2": {data}}
                    for record in valid_data.values():
                        if isinstance(record, dict):
                            # Use date_key if record doesn't have its own date
                            if 'date' not in record:
                                record['date'] = date_key
                            all_records.append(record)
                elif isinstance(valid_data, list):
                    # Array-like: [{"id": {data}}, ...] or [{data}, {data}]
                    for item in valid_data:
                        if isinstance(item, dict):
                            # Check if it's a wrapper {"id": {data}} or just {data}
                            # A simple heuristic: check for known keys like 'vehicle_count'
                            if 'vehicle_count' in item:
                                if 'date' not in item:
                                    item['date'] = date_key
                                all_records.append(item)
                            else:
                                for sub_item in item.values():
                                     if isinstance(sub_item, dict):
                                         if 'date' not in sub_item:
                                             sub_item['date'] = date_key
                                         all_records.append(sub_item)

        if not all_records:
            return {
                "vehicleCount": 0,
                "time": "N/A",
                "congestion": [],
                "report": [],
                "graph_data": []
            }

        # Aggregation
        total_vehicles = 0
        reasons = []
        reports_map = {} # deduplicate by reason
        timestamps = []

        for record in all_records:
            # Vehicle Count
            v_count = record.get('vehicle_count', 0)
            if isinstance(v_count, (int, float)):
                 total_vehicles += int(v_count)
            
            # Reasons for congestion stats
            # 'reason' often contains the error, 'status' or 'suggestion' might be useful too
            # The user output example maps "Wrong Parking" from "reason" or "status"
            # We'll use 'reason' if available, otherwise 'status'
            reason = record.get('reason', 'Unknown')
            # Clean up reason for better grouping (simple extraction)
            short_reason = reason.split(':')[0] if ':' in reason else reason
            # The sample output had formatted names like "Wrong Parking". 
            # We will use the 'status' if it seems more categorical, or 'reason'.
            # Sample: reason="OpenRouter...", status="vehicles moving slowly". 
            # The User's Sample Output maps this to "Wrong Parking"? 
            # Wait, the user sample INPUT has "OpenRouter error" but OUTPUT has "Wrong Parking".
            # This implies the user wants me to simulated logic or map specific strings.
            # I will assume "status" is the category if present, strictly falling back to reason.
            
            category = record.get('status', short_reason)
            reasons.append(category)

            # Report generation
            if category not in reports_map:
                # Create readable reason - combine category with the actual reason
                if reason != category and reason != 'Unknown':
                    readable_reason = f"{category} ({reason})"
                else:
                    readable_reason = category
                reports_map[category] = {
                    "reason": readable_reason,
                    "suggestion": record.get('suggestion', "No suggestion provided")
                }

            # Graph Data - include date and congestion reason
            ts = record.get('timestamp')
            if ts:
                timestamps.append({
                    't': ts,
                    'v': v_count,
                    'date': record.get('date', 'Unknown'),
                    'reason': category
                })

        # Calculate Percentages
        congestion_stats = []
        reason_counts = Counter(reasons)
        total_reasons = sum(reason_counts.values())
        
        for r, count in reason_counts.items():
            percentage = round((count / total_reasons) * 100, 1) if total_reasons > 0 else 0
            congestion_stats.append({
                "name": r,
                "percentage": percentage
            })

        # Format Time (Latest) - use 12-hour format like "3:30"
        timestamps.sort(key=lambda x: x['t'])
        latest_time_str = "N/A"
        if timestamps:
            latest_ts = timestamps[-1]['t']
            dt_obj = datetime.fromtimestamp(latest_ts)
            # Use %-H for 12-hour without leading zero on Windows use %#H
            hour = dt_obj.hour % 12 or 12  # Convert to 12-hour format
            minute = dt_obj.strftime("%M")
            latest_time_str = f"{hour}:{minute}"

        # Graph Data Formatting - use percentage from congestion stats
        # Create a lookup for reason percentages
        reason_percentages = {c['name']: c['percentage'] for c in congestion_stats}
        
        graph_data = []
        for point in timestamps:
            dt = datetime.fromtimestamp(point['t'])
            hour_g = dt.hour % 12 or 12
            time_label = f"{hour_g}:{dt.strftime('%M:%S')}"
            # Combine time and date into single timestamp field
            timestamp_str = f"{time_label},{point['date']}"
            graph_data.append({
                "timestamp": timestamp_str,
                "percentage": reason_percentages.get(point['reason'], 0),
                "reason": point['reason']
            })

        return {
            "vehicleCount": total_vehicles,
            "time": latest_time_str,
            "congestion": congestion_stats,
            "report": list(reports_map.values()),
            "graph": graph_data
        }

if __name__ == "__main__":
    # Test with the sample provided (cleaned up)
    sample_json = """
    {
      "01-08-2025": {
        "-0WaCEPkqzD7SO4TLVzM": {
          "date": "01-08-2025",
          "reason": "Observed: Illegal Parking",
          "status": "Wrong Parking",
          "suggestion": "Remove parked vehicles",
          "time": "20:46",
          "timestamp": 1754061402.5369713,
          "vehicle_count": 1
        },
        "-0WaCEPkqzD7SO4TLVzN": {
          "date": "01-08-2025",
          "reason": "Signal malfunction",
          "status": "Signal Delay",
          "suggestion": "Optimize signal",
          "time": "20:47",
          "timestamp": 1754061462.5369713,
          "vehicle_count": 5
        }
      }
    }
    """
    processor = TrafficProcessor()
    data = processor.get_data_from_json(sample_json)
    result = processor.process_data(data)
    print(json.dumps(result, indent=2))
