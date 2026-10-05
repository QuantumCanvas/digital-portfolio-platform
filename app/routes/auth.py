import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User, Skill

auth_bp = Blueprint("auth", __name__)

DEFAULT_SKILLS = [
    ("Frontend Architecture", 60, "Frontend"),
    ("Backend & APIs", 55, "Backend"),
    ("AI/ML Integration", 40, "AI/ML"),
    ("System Design", 50, "Architecture"),
    ("Cloud & DevOps", 45, "DevOps"),
    ("UI/UX & Micro-interactions", 65, "Design"),
]


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()
    username = (data.get("username") or "").strip().lower()
    title = (data.get("title") or "Aspiring Builder").strip()
    bio = (data.get("bio") or "").strip()
    target_role_id = data.get("targetRoleId") or "fullstack-ai"

    if not email or not password or not name or not username:
        return jsonify({"error": "name, username, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400
    if not re.match(r"^[a-z0-9_]+$", username):
        return jsonify({"error": "username may only contain lowercase letters, numbers and underscores"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "an account with that email already exists"}), 409
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "that username is taken"}), 409

    user = User(
        email=email, username=username, name=name, title=title, bio=bio,
        target_role_id=target_role_id,
        avatar=data.get("avatar", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80"),
        cover_image="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=80",
        location=data.get("location", ""),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    for skill_name, score, category in DEFAULT_SKILLS:
        db.session.add(Skill(user_id=user.id, name=skill_name, score=score, category=category))

    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict(viewer_id=user.id)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict(viewer_id=user.id)})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict(viewer_id=user_id))
