#!/usr/bin/env python3
"""
Mini-Ultra Unified Launcher
Start any mode: api, web, cli, or full stack.

Usage:
    python mini_ultra_launch.py --mode api
    python mini_ultra_launch.py --mode web
    python mini_ultra_launch.py --mode cli
    python mini_ultra_launch.py --mode full
"""
import argparse
import sys
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_core import MiniUltraAgent
from utils.logger import log_info, log_error


def parse_args():
    parser = argparse.ArgumentParser(description="Mini-Ultra Agent Launcher")
    parser.add_argument(
        "--mode", choices=["api", "web", "cli", "full"],
        default="cli", help="Execution mode (default: cli)"
    )
    parser.add_argument("--api-port", type=int, default=5000, help="API server port")
    parser.add_argument("--web-port", type=int, default=8080, help="Web GUI port")
    parser.add_argument("--host", default="0.0.0.0", help="Server bind address")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--config", default="mini_ultra_config.json", help="Config file path")
    return parser.parse_args()


def run_api_mode(agent, host, port, debug):
    """Start API server only."""
    from api.server import run_api_server
    log_info("launcher", f"Starting API server on {host}:{port}")
    run_api_server(agent, host=host, port=port, debug=debug)


def run_web_mode(agent, host, port, debug):
    """Start Web GUI server (includes API endpoints)."""
    from web_server import run_web_server
    log_info("launcher", f"Starting Web GUI on {host}:{port}")
    run_web_server(agent, host=host, port=port, debug=debug)


def run_cli_mode(agent):
    """Start interactive CLI."""
    from main import run_cli
    run_cli(agent)


def run_full_mode(agent, host, api_port, web_port, debug):
    """Start full stack: API + Web GUI in separate threads."""
    log_info("launcher", "Starting full stack mode...")

    # Start API server in background thread
    from api.server import create_app as create_api_app
    api_app = create_api_app(agent)

    def start_api():
        log_info("launcher", f"API server starting on {host}:{api_port}")
        api_app.run(host=host, port=api_port, debug=False, use_reloader=False)

    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    # Start Web GUI on main thread
    from web_server import run_web_server
    log_info("launcher", f"Web GUI starting on {host}:{web_port}")
    log_info("launcher", f"API: http://{host}:{api_port} | Web: http://{host}:{web_port}/gui")
    run_web_server(agent, host=host, port=web_port, debug=debug)


def main():
    args = parse_args()

    print(r"""
    ╔══════════════════════════════════════╗
    ║         MINI-ULTRA AGENT             ║
    ║     Lightweight AI Assistant         ║
    ╚══════════════════════════════════════╝
    """)

    log_info("launcher", f"Mode: {args.mode}")

    try:
        agent = MiniUltraAgent(config_path=args.config)
        log_info("launcher", f"Agent initialized. Tools: {len(agent.tools)}")

        if args.mode == "api":
            run_api_mode(agent, args.host, args.api_port, args.debug)
        elif args.mode == "web":
            run_web_mode(agent, args.host, args.web_port, args.debug)
        elif args.mode == "cli":
            run_cli_mode(agent)
        elif args.mode == "full":
            run_full_mode(agent, args.host, args.api_port, args.web_port, args.debug)

    except KeyboardInterrupt:
        log_info("launcher", "Shutdown requested")
    except Exception as e:
        log_error("launcher", f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
