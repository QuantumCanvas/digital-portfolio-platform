import json
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import RoadmapNode, UserNodeProgress, User, Skill, FeedPost

roadmaps_bp = Blueprint("roadmaps", __name__)


@roadmaps_bp.route("/<role_id>", methods=["GET"])
@jwt_required(optional=True)
def get_roadmap(role_id):
    from flask_jwt_extended import get_jwt_identity as gid
    user_id = int(gid()) if gid() else None
    nodes = RoadmapNode.query.filter_by(role_id=role_id).order_by(RoadmapNode.order_index).all()
    return jsonify([n.to_dict(user_id=user_id) for n in nodes])


@roadmaps_bp.route("/<role_id>/<node_id>/complete", methods=["POST"])
@jwt_required()
def complete_node(role_id, node_id):
    user_id = int(get_jwt_identity())
    node = RoadmapNode.query.filter_by(id=node_id, role_id=role_id).first_or_404()
    user = User.query.get_or_404(user_id)

    progress = UserNodeProgress.query.filter_by(user_id=user_id, node_id=node_id).first()
    current_status = progress.status if progress else node.default_status
    if current_status == "mastered":
        return jsonify({"error": "node already mastered"}), 409

    if progress:
        progress.status = "mastered"
    else:
        db.session.add(UserNodeProgress(user_id=user_id, node_id=node_id, status="mastered"))

    # Award XP and level up if the threshold is crossed.
    user.xp += node.xp
    leveled_up = False
    if user.xp >= user.next_level_xp:
        user.level += 1
        user.next_level_xp = int(user.next_level_xp * 1.35)
        leveled_up = True

    # Bump related skill scores, same logic as the original client-side app.
    for skill in user.skills:
        if skill.category.lower() in node.category.lower() or node.title.lower().find(skill.name.lower()) != -1:
            skill.score = min(100, skill.score + 8)

    # Post a milestone to the feed, same as the original app.
    db.session.add(FeedPost(
        user_id=user_id, category="Skill Milestone",
        content=f"Just completed the skill node \"{node.title}\" in the roadmap! Gained +{node.xp} XP!",
        tags_json=json.dumps(["Skill Milestone", node.category]),
    ))

    db.session.commit()
    return jsonify({
        "node": node.to_dict(user_id=user_id),
        "xpGained": node.xp,
        "leveledUp": leveled_up,
        "user": user.to_dict(viewer_id=user_id),
    })
