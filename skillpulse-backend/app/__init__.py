import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_object="config.Config"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    os.makedirs(app.instance_path, exist_ok=True)

    CORS(app, supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.roadmaps import roadmaps_bp
    from app.routes.circles import circles_bp
    from app.routes.feed import feed_bp
    from app.routes.peers import peers_bp
    from app.routes.meta import meta_bp
    from app.routes.connections import connections_bp
    from app.routes.portfolio import portfolio_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(roadmaps_bp, url_prefix="/api/roadmaps")
    app.register_blueprint(circles_bp, url_prefix="/api/circles")
    app.register_blueprint(feed_bp, url_prefix="/api/feed")
    app.register_blueprint(peers_bp, url_prefix="/api/peers")
    app.register_blueprint(meta_bp, url_prefix="/api/meta")
    app.register_blueprint(connections_bp, url_prefix="/api/connections")
    app.register_blueprint(portfolio_bp, url_prefix="/portfolio")

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    # Serve the single-page frontend from /frontend so the whole app runs
    # from one command (python run.py) at http://localhost:5000/
    from flask import send_from_directory
    frontend_dir = os.path.join(os.path.dirname(app.root_path), "frontend")

    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    with app.app_context():
        db.create_all()
        _add_missing_columns()
        from app.seed import run_seed
        run_seed()

    return app


def _add_missing_columns():
    """db.create_all() creates new tables but never alters existing ones, so an
    app.db from an earlier version would be missing the portfolio columns."""
    from sqlalchemy import inspect, text
    existing = {c["name"] for c in inspect(db.engine).get_columns("users")}
    wanted = {
        "portfolio_enabled": "BOOLEAN DEFAULT 0",
        "portfolio_theme": "VARCHAR(20) DEFAULT 'grape'",
    }
    for name, ddl in wanted.items():
        if name not in existing:
            db.session.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
    db.session.commit()
