import json
from traffic_processor import TrafficProcessor
import unittest

class TestTrafficProcessor(unittest.TestCase):
    def test_sample_processing(self):
        # This matches the structure of the sample provided by the user (corrected syntax)
        sample_json = """
        {
          "01-08-2025": {
            "-0WaCEPkqzD7SO4TLVzM": {
              "date": "01-08-2025",
              "reason": "OpenRouter error: Payment Required",
              "status": "vehicles moving slowly",
              "suggestion": "Check traffic lights",
              "time": "20:46",
              "timestamp": 1754061402.536,
              "vehicle_count": 1
            },
            "-0WaCEPkqzD7SO4TLVzN": {
              "date": "01-08-2025",
              "reason": "Signal Issue",
              "status": "Signal Delay",
              "suggestion": "Optimize timing",
              "time": "20:50",
              "timestamp": 1754061642.536,
              "vehicle_count": 5
            }
          }
        }
        """
        processor = TrafficProcessor()
        data = processor.get_data_from_json(sample_json)
        result = processor.process_data(data)

        # Check Keys
        self.assertIn('vehicleCount', result)
        self.assertIn('time', result)
        self.assertIn('congestion', result)
        self.assertIn('report', result)
        self.assertIn('graph', result)  # Added by us for the app

        # Check Values
        self.assertEqual(result['vehicleCount'], 6)
        
        # Check Congestion logic
        # We expect 2 items: "vehicles moving slowly" and "Signal Delay"
        names = [c['name'] for c in result['congestion']]
        self.assertIn("vehicles moving slowly", names)
        self.assertIn("Signal Delay", names)

        # Check percentages (each 50% since count is 1 for each category logic)
        # Wait, my logic counts occurrences of the category. 
        # Here we have 2 records. 1 "vehicles moving slowly", 1 "Signal Delay".
        # So 50/50 split.
        for c in result['congestion']:
            self.assertEqual(c['percentage'], 50.0)

        print("\nTest Output Result:\n", json.dumps(result, indent=2))

if __name__ == '__main__':
    unittest.main()
