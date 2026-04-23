#!/usr/bin/env python3
"""
Mini-Ultra Agent - Main Entry Point
Lightweight version of the ULTRON Agent.
"""
import sys
import signal
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_core import MiniUltraAgent
from utils.logger import log_info, log_error


def setup_signal_handlers():
    """Setup graceful shutdown on signals."""
    def handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def run_cli(agent: MiniUltraAgent):
    """Run the agent in interactive CLI mode."""
    print("\n" + "=" * 60)
    print("  Mini-Ultra Agent - Interactive CLI")
    print("  Type 'quit' to exit, 'help' for commands")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("\033[36mYou:\033[0m ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            elif user_input.lower() == "help":
                print_cli_help()
                continue
            elif user_input.lower() == "health":
                import json
                print(json.dumps(agent.health_check(), indent=2))
                continue
            elif user_input.lower() == "tools":
                for tool in agent.get_tool_list():
                    print(f"  - {tool['name']}: {tool['description']}")
                continue
            elif user_input.lower() == "diagnose":
                import json
                print(json.dumps(agent.self_diagnosis(), indent=2))
                continue
            elif user_input.lower() == "reset":
                agent.reset_conversation()
                print("Conversation reset.")
                continue
            elif user_input.lower() == "memory":
                if agent.memory:
                    import json
                    print(json.dumps(agent.memory.stats(), indent=2))
                else:
                    print("Memory not enabled.")
                continue

            response = agent.process_message(user_input)
            print(f"\033[32mMini-Ultra:\033[0m {response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


def print_cli_help():
    print("""
Commands:
  help      - Show this help
  health    - Run health check
  tools     - List available tools
  diagnose  - Run self-diagnosis
  memory    - Show memory stats
  reset     - Reset conversation
  quit      - Exit
""")


def main() -> int:
    """Main entry point."""
    setup_signal_handlers()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    log_info("main", "Starting Mini-Ultra Agent...")

    try:
        agent = MiniUltraAgent()
        log_info("main", f"Agent ready. Status: {agent.status.value}")

        # Check launch mode
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower().strip("-")
            if mode == "web":
                from web_server import run_web_server
                run_web_server(agent)
            elif mode == "api":
                from api.server import run_api_server
                run_api_server(agent)
            elif mode == "cli":
                run_cli(agent)
            else:
                print(f"Unknown mode: {mode}")
                print("Usage: python main.py [--web|--api|--cli]")
                return 1
        else:
            # Default: CLI mode
            run_cli(agent)

        return 0

    except Exception as e:
        log_error("main", f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
