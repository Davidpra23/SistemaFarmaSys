
import webview
import threading
from app import app

def start_flask():
    # Use a fixed port for the window URL
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    webview.create_window("FarmaSys - Desktop", "http://127.0.0.1:5000", width=1200, height=800, resizable=True)
    webview.start()
