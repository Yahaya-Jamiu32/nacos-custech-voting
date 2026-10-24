import os
from datetime import timedelta
from flask import Flask, jsonify
from sqlalchemy.pool import NullPool
from .models import db

def _find_db_url():
    """Find the database address whatever prefix Vercel/Neon used (e.g. DATABASE_URL, STORAGE_DATABASE_URL)."""
    env = os.environ
    for k in ("DATABASE_URL", "POSTGRES_URL"):
        if env.get(k): return env[k]
    for suffix in ("DATABASE_URL", "POSTGRES_URL"):
        for k in sorted(env):
            if k.endswith("_" + suffix) and env[k] and "UNPOOLED" not in k and "NON_POOLING" not in k: return env[k]
    return ""

def create_app(config=None):
    app = Flask(__name__)
    url = _find_db_url()
    if url.startswith("postgres://"): url = url.replace("postgres://", "postgresql://", 1)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"), PHONE_PEPPER=os.environ.get("PHONE_PEPPER"),
        ADMIN_MATRIC=os.environ.get("ADMIN_MATRIC") or "23L1CSS0055", ADMIN_PHONE=os.environ.get("ADMIN_PHONE") or "07036779507",   # server-side only; env vars override
        ADMIN_PASSWORD_HASH=os.environ.get("ADMIN_PASSWORD_HASH", ""),
        SQLALCHEMY_DATABASE_URI=url,
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": NullPool, "connect_args": {"sslmode": "require", "connect_timeout": 10}} if url.startswith("postgresql") else {},
        AUTO_INIT_DB=os.environ.get("AUTO_INIT_DB", "1") == "1",
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2), LOGIN_MAX_FAILS=8, MAX_CONTENT_LENGTH=1024 * 1024)
    if config: app.config.update(config)
    for k in ("SECRET_KEY", "PHONE_PEPPER", "SQLALCHEMY_DATABASE_URI"):
        if not app.config.get(k): raise RuntimeError(f"Missing required setting: {k}")
    if not app.config["ADMIN_PASSWORD_HASH"] and os.environ.get("ADMIN_PASSWORD"):   # lets you deploy without any local tooling
        pw = os.environ["ADMIN_PASSWORD"]
        if len(pw) < 12: raise RuntimeError("ADMIN_PASSWORD must be at least 12 characters")
        from werkzeug.security import generate_password_hash
        app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(pw)
    db.init_app(app)
    from .routes import bp
    app.register_blueprint(bp)
    if app.config["AUTO_INIT_DB"]:   # tables + categories are created on first start, no laptop needed
        from .seed import seed
        with app.app_context():
            try: seed()
            except Exception:
                db.session.rollback(); app.logger.exception("DB init failed; check DATABASE_URL")

    @app.errorhandler(Exception)
    def _err(e):
        code = getattr(e, "code", 500)
        if code == 500: app.logger.exception("Unhandled error")
        return jsonify(error="Server error" if code == 500 else getattr(e, "name", "Error")), code
    return app
