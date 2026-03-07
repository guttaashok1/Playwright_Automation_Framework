"""Serve the reports/ directory on the port assigned via PORT env var."""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

port = int(os.environ.get("PORT", 8080))
os.chdir(os.path.join(os.path.dirname(__file__), "reports"))
print(f"Serving reports/ on http://0.0.0.0:{port}", flush=True)
HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler).serve_forever()
