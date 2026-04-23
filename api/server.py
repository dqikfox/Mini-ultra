"""
Mini-Ultra REST API Server
Flask-based API with /health, /chat, /tools, /memory endpoints.
"""
from flask import Flask, request, jsonify
from datetime import datetime
from agent_core import MiniUltraAgent
from utils.logger import log_info, log_error


def create_app(agent: MiniUltraAgent = None) -> Flask:
    """Create and configure the Flask API app."""
    app = Flask(__name__)

    if agent is None:
        agent = MiniUltraAgent()

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "name": "Mini-Ultra API",
            "version": agent.config.get("version", "1.0.0"),
            "status": agent.status.value,
            "endpoints": ["/health", "/chat", "/tools", "/memory", "/diagnosis"],
        })

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify(agent.health_check())

    @app.route("/chat", methods=["POST"])
    def chat():
        """Chat with the agent."""
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing 'message' field"}), 400

        message = data["message"]
        log_info("api", f"Chat request: {message[:80]}...")

        try:
            response = agent.process_message(message)
            return jsonify({
                "response": response,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            log_error("api", f"Chat error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/tools", methods=["GET"])
    def tools():
        """List available tools."""
        return jsonify({
            "tools": agent.get_tool_list(),
            "count": len(agent.tools),
        })

    @app.route("/tools/<tool_name>/execute", methods=["POST"])
    def execute_tool(tool_name):
        """Execute a specific tool directly."""
        data = request.get_json() or {}
        result = agent._execute_tool(tool_name, data)
        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code

    @app.route("/memory", methods=["GET"])
    def memory_list():
        """Get recent memories."""
        limit = request.args.get("limit", 20, type=int)
        if agent.memory:
            return jsonify({
                "memories": agent.memory.get_recent(limit),
                "stats": agent.memory.stats(),
            })
        return jsonify({"error": "Memory not enabled"}), 404

    @app.route("/memory/search", methods=["GET"])
    def memory_search():
        """Search memories."""
        query = request.args.get("q", "")
        limit = request.args.get("limit", 10, type=int)
        if not query:
            return jsonify({"error": "Missing 'q' parameter"}), 400
        if agent.memory:
            results = agent.memory.search(query, limit)
            return jsonify({"results": results, "query": query, "count": len(results)})
        return jsonify({"error": "Memory not enabled"}), 404

    @app.route("/memory", methods=["POST"])
    def memory_add():
        """Add a memory entry."""
        data = request.get_json()
        if not data or "content" not in data:
            return jsonify({"error": "Missing 'content' field"}), 400
        if agent.memory:
            entry = agent.memory.add(
                content=data["content"],
                category=data.get("category", "manual"),
                metadata=data.get("metadata"),
            )
            return jsonify(entry), 201
        return jsonify({"error": "Memory not enabled"}), 404

    @app.route("/memory", methods=["DELETE"])
    def memory_clear():
        """Clear all memories."""
        if agent.memory:
            agent.memory.clear()
            return jsonify({"message": "All memories cleared"})
        return jsonify({"error": "Memory not enabled"}), 404

    @app.route("/diagnosis", methods=["GET"])
    def diagnosis():
        """Run self-diagnosis on all subsystems."""
        return jsonify(agent.self_diagnosis())

    @app.route("/conversation/reset", methods=["POST"])
    def reset_conversation():
        """Reset conversation history."""
        agent.reset_conversation()
        return jsonify({"message": "Conversation reset"})

    return app


def run_api_server(agent: MiniUltraAgent = None, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start the API server."""
    app = create_app(agent)
    log_info("api", f"Starting Mini-Ultra API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
