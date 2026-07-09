import os
import sys
import webbrowser
from threading import Timer
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Import the existing app from server.py
from server import app

# Determine base path whether running as script or bundled executable
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the frontend UI folder
# Assuming run_app.py is in the backend folder, and ui_ux_design is one level up
ui_dir = os.path.join(os.path.dirname(base_dir), "ui_ux_design")

# Mount the static files to serve the frontend on the root URL
if os.path.exists(ui_dir):
    app.mount("/", StaticFiles(directory=ui_dir, html=True), name="ui")
else:
    print(f"Warning: UI directory not found at {ui_dir}")

def open_browser():
    """Opens the default web browser to the local app URL"""
    webbrowser.open_new("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("Starting PACE Application...")
    # Delay browser opening slightly to let server start, but skip on Railway/Cloud
    if not os.environ.get("RAILWAY_PROJECT_ID") and not os.environ.get("PORT"):
        Timer(1.5, open_browser).start()
    
    # Run the server
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
