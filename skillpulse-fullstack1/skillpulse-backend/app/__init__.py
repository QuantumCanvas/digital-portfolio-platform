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

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(roadmaps_bp, url_prefix="/api/roadmaps")
    app.register_blueprint(circles_bp, url_prefix="/api/circles")
    app.register_blueprint(feed_bp, url_prefix="/api/feed")
    app.register_blueprint(peers_bp, url_prefix="/api/peers")
    app.register_blueprint(meta_bp, url_prefix="/api/meta")

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
        from app.seed import run_seed
        run_seed()

    return app
