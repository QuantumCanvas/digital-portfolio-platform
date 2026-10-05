from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import GrowthCircle, CircleMembership, Discussion

circles_bp = Blueprint("circles", __name__)


@circles_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_circles():
    from flask_jwt_extended import get_jwt_identity as gid
    user_id = int(gid()) if gid() else None
    circles = GrowthCircle.query.all()
    return jsonify([c.to_dict(user_id=user_id) for c in circles])


@circles_bp.route("/<circle_id>/join", methods=["POST"])
@jwt_required()
def toggle_join(circle_id):
    user_id = int(get_jwt_identity())
    circle = GrowthCircle.query.get_or_404(circle_id)
    existing = CircleMembership.query.filter_by(circle_id=circle_id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"isJoined": False, "membersCount": circle.memberships.count()})
    db.session.add(CircleMembership(circle_id=circle_id, user_id=user_id))
    db.session.commit()
    return jsonify({"isJoined": True, "membersCount": circle.memberships.count()})


@circles_bp.route("/<circle_id>/discussions", methods=["POST"])
@jwt_required()
def add_discussion(circle_id):
    user_id = int(get_jwt_identity())
    GrowthCircle.query.get_or_404(circle_id)
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    d = Discussion(circle_id=circle_id, author_id=user_id, title=title)
    db.session.add(d)
    db.session.commit()
    return jsonify(d.to_dict()), 201
