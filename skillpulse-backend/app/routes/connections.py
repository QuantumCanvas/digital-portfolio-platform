from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Connection, connection_between, connection_status

connections_bp = Blueprint("connections", __name__)


def _person(user, when):
    d = user.to_public_dict()
    d["since"] = when.isoformat() if when else None
    return d


@connections_bp.route("", methods=["GET"])
@jwt_required()
def list_connections():
    """Everything the Network page needs in one call."""
    me = int(get_jwt_identity())
    rows = Connection.query.filter(
        db.or_(Connection.requester_id == me, Connection.addressee_id == me)
    ).order_by(Connection.created_at.desc()).all()

    connected, incoming, outgoing = [], [], []
    for c in rows:
        if c.status == "accepted":
            other = c.addressee if c.requester_id == me else c.requester
            connected.append(_person(other, c.responded_at or c.created_at))
        elif c.addressee_id == me:
            incoming.append(_person(c.requester, c.created_at))
        else:
            outgoing.append(_person(c.addressee, c.created_at))
    return jsonify({"connections": connected, "incoming": incoming, "outgoing": outgoing})


@connections_bp.route("/request/<int:user_id>", methods=["POST"])
@jwt_required()
def send_request(user_id):
    me = int(get_jwt_identity())
    if user_id == me:
        return jsonify({"error": "you can't connect with yourself"}), 400
    User.query.get_or_404(user_id)

    existing = connection_between(me, user_id)
    if existing:
        if existing.status == "accepted":
            return jsonify({"error": "you are already connected"}), 409
        if existing.requester_id == me:
            return jsonify({"error": "request already sent"}), 409
        # They already asked to connect with us, so sending one back means "yes".
        existing.status = "accepted"
        existing.responded_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "connected"})

    db.session.add(Connection(requester_id=me, addressee_id=user_id, status="pending"))
    db.session.commit()
    return jsonify({"status": "pending_out"}), 201


@connections_bp.route("/<int:user_id>/accept", methods=["POST"])
@jwt_required()
def accept_request(user_id):
    me = int(get_jwt_identity())
    c = Connection.query.filter_by(
        requester_id=user_id, addressee_id=me, status="pending"
    ).first()
    if not c:
        return jsonify({"error": "no pending request from that user"}), 404
    c.status = "accepted"
    c.responded_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"status": "connected"})


@connections_bp.route("/<int:user_id>/decline", methods=["POST"])
@jwt_required()
def decline_request(user_id):
    me = int(get_jwt_identity())
    c = Connection.query.filter_by(
        requester_id=user_id, addressee_id=me, status="pending"
    ).first()
    if not c:
        return jsonify({"error": "no pending request from that user"}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "none"})


@connections_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def remove_connection(user_id):
    """Cancel a request I sent, or remove an existing connection."""
    me = int(get_jwt_identity())
    c = connection_between(me, user_id)
    if not c:
        return jsonify({"error": "no connection with that user"}), 404
    if c.status == "pending" and c.addressee_id == me:
        # Incoming requests are answered with accept/decline, not deleted here.
        return jsonify({"error": "use accept or decline for incoming requests"}), 400
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "none"})
