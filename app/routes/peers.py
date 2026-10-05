from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

peers_bp = Blueprint("peers", __name__)


def _peer_dict(user, viewer_skills_by_name):
    sorted_skills = sorted(user.skills, key=lambda s: s.score, reverse=True)
    strong = [s.name for s in sorted_skills[:3]]
    # "Seeking" = this peer's weakest skills, a reasonable proxy for what they'd
    # want help with from a match.
    seeking = [s.name for s in sorted_skills[-2:]] if len(sorted_skills) >= 2 else []

    # Simple compatibility score: peers are a good match if their strong skills
    # cover what the viewer is weak in, and vice versa.
    overlap_bonus = 0
    for s in user.skills:
        viewer_score = viewer_skills_by_name.get(s.name.lower())
        if viewer_score is not None and abs(viewer_score - s.score) > 25:
            overlap_bonus += 5
    compatibility = min(97, 70 + overlap_bonus)

    return {
        "id": user.id, "name": user.name, "title": user.title, "avatar": user.avatar,
        "level": user.level, "strongSkills": strong, "seekingSkills": seeking,
        "compatibility": f"{compatibility}% Match for Pair Building",
    }


@peers_bp.route("", methods=["GET"])
@jwt_required()
def list_peers():
    viewer_id = int(get_jwt_identity())
    viewer = User.query.get_or_404(viewer_id)
    viewer_skills_by_name = {s.name.lower(): s.score for s in viewer.skills}

    peers = User.query.filter(User.id != viewer_id, User.open_for_peers.is_(True)).all()
    return jsonify([_peer_dict(p, viewer_skills_by_name) for p in peers])
