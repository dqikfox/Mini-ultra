"""
Mini-Ultra Web Server
Serves the Web GUI and proxies API calls to the agent.
"""
import os
from flask import Flask, send_from_directory
from agent_core import MiniUltraAgent
from api.server import create_app
from utils.logger import log_info


def create_web_app(agent: MiniUltraAgent = None) -> Flask:
    """Create a Flask app that serves both the Web GUI and API endpoints."""
    # Create the API app (includes all /chat, /health, etc. routes)
    app = create_app(agent)

    # Serve static files from web_gui/
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_gui")

    @app.route("/gui")
    @app.route("/gui/")
    def serve_gui():
        return send_from_directory(gui_dir, "index.html")

    @app.route("/gui/<path:filename>")
    def serve_gui_static(filename):
        return send_from_directory(gui_dir, filename)

    # Also serve GUI at root for convenience
    @app.route("/app")
    @app.route("/app/")
    def serve_app():
        return send_from_directory(gui_dir, "index.html")

    return app


def run_web_server(agent: MiniUltraAgent = None, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
    """Start the web server with GUI and API."""
    app = create_web_app(agent)
    log_info("web_server", f"Starting Mini-Ultra Web GUI on http://{host}:{port}/gui")
    log_info("web_server", f"API available at http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web_server()
