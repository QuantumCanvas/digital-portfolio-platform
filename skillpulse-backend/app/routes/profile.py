import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models import User, Skill, Project, ProjectClap, connection_status
from app.utils import safe_url

profile_bp = Blueprint("profile", __name__)


def _optional_viewer_id():
    from flask_jwt_extended import verify_jwt_in_request
    try:
        verify_jwt_in_request(optional=True)
        ident = get_jwt_identity()
        return int(ident) if ident else None
    except Exception:
        return None


@profile_bp.route("/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    viewer_id = _optional_viewer_id()
    data = user.to_dict(viewer_id=viewer_id)
    data["connectionStatus"] = connection_status(viewer_id, user.id)
    # Only the owner can see their portfolio link while it is unpublished.
    if not user.portfolio_enabled and viewer_id != user.id:
        data["portfolio"] = {"enabled": False}
    return jsonify(data)


@profile_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json() or {}
    simple_fields = {
        "name": "name", "title": "title", "bio": "bio", "location": "location",
        "avatar": "avatar", "coverImage": "cover_image", "targetRoleId": "target_role_id",
        "openForPeers": "open_for_peers",
    }
    for incoming, attr in simple_fields.items():
        if incoming in data:
            setattr(user, attr, data[incoming])
    if "socials" in data and isinstance(data["socials"], dict):
        socials = data["socials"]
        user.github = socials.get("github", user.github)
        user.twitter = socials.get("twitter", user.twitter)
        user.website = socials.get("website", user.website)
    db.session.commit()
    return jsonify(user.to_dict(viewer_id=user.id))


@profile_bp.route("/me/portfolio", methods=["PUT"])
@jwt_required()
def update_portfolio():
    """Publish / unpublish the generated portfolio page and pick its theme."""
    from app.routes.portfolio import THEMES
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json() or {}
    if "theme" in data:
        if data["theme"] not in THEMES:
            return jsonify({"error": "unknown theme"}), 400
        user.portfolio_theme = data["theme"]
    if "enabled" in data:
        user.portfolio_enabled = bool(data["enabled"])
    db.session.commit()
    return jsonify(user.to_dict(viewer_id=user.id))


@profile_bp.route("/me/skills", methods=["POST"])
@jwt_required()
def add_skill():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    if Skill.query.filter_by(user_id=user_id, name=name).first():
        return jsonify({"error": "skill already added"}), 409
    skill = Skill(user_id=user_id, name=name, score=int(data.get("score", 30)),
                  category=data.get("category", "General"))
    db.session.add(skill)
    db.session.commit()
    return jsonify(skill.to_dict()), 201


@profile_bp.route("/me/skills/<int:skill_id>", methods=["DELETE"])
@jwt_required()
def delete_skill(skill_id):
    user_id = int(get_jwt_identity())
    skill = Skill.query.filter_by(id=skill_id, user_id=user_id).first_or_404()
    db.session.delete(skill)
    db.session.commit()
    return jsonify({"status": "deleted"})


@profile_bp.route("/me/projects", methods=["POST"])
@jwt_required()
def add_project():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    for field in ("demoUrl", "repoUrl"):
        if data.get(field) and not safe_url(data[field]):
            return jsonify({"error": f"{field} must start with http:// or https://"}), 400
    project = Project(
        user_id=user_id, title=title, tagline=data.get("tagline", ""),
        description=data.get("description", ""), demo_url=data.get("demoUrl", ""),
        repo_url=data.get("repoUrl", ""),
        image=data.get("image", "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&auto=format&fit=crop&q=80"),
        tags_json=json.dumps(data.get("tags", [])),
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict(viewer_id=user_id)), 201


@profile_bp.route("/me/projects/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    db.session.delete(project)
    db.session.commit()
    return jsonify({"status": "deleted"})


@profile_bp.route("/projects/<int:project_id>/clap", methods=["POST"])
@jwt_required()
def clap_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)
    existing = ProjectClap.query.filter_by(project_id=project_id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"hasClapped": False, "claps": project.claps.count()})
    db.session.add(ProjectClap(project_id=project_id, user_id=user_id))
    db.session.commit()
    return jsonify({"hasClapped": True, "claps": project.claps.count()})
