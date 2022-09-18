from http.server import BaseHTTPRequestHandler
import os
import json

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
EXPORTER_PORT = 30026
EXPORTER_ADDRESS = "0.0.0.0"
READINGS_DATA_PATH = os.path.join(
    CURRENT_SCRIPT_PATH, 'pitmaster_readings.json')


class AllReadingsServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if not os.path.exists(READINGS_DATA_PATH):
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(
                bytes(f"Could not find file '{READINGS_DATA_PATH}'", "utf-8"))
        else:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header("Content-type", "application/json")
            self.end_headers()
            payload = None
            with open(READINGS_DATA_PATH, 'r') as f:
                payload = json.load(f)
            self.wfile.write(bytes(json.dumps(payload), "utf-8"))
