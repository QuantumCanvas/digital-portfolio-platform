from flask import Blueprint, jsonify
from app.models import TargetRole, MarketTrend

meta_bp = Blueprint("meta", __name__)


@meta_bp.route("/target-roles", methods=["GET"])
def target_roles():
    return jsonify([r.to_dict() for r in TargetRole.query.all()])


@meta_bp.route("/market-trends", methods=["GET"])
def market_trends():
    return jsonify([t.to_dict() for t in MarketTrend.query.all()])
