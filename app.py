import re

try:
    from votingapp import create_app
    app = create_app()
except Exception as exc:  # show WHY the server failed to start, instead of Vercel's blank error page
    from flask import Flask, jsonify
    _msg = re.sub(r"postgres(ql)?://\S+", "[database-url-hidden]", f"{type(exc).__name__}: {exc}")[:300]
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _startup_error(path):
        return jsonify(ok=False, startup_error=_msg), 500
