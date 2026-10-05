import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import FeedPost, PostClap, Comment
from app.utils import safe_url

feed_bp = Blueprint("feed", __name__)


@feed_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_feed():
    from flask_jwt_extended import get_jwt_identity as gid
    viewer_id = int(gid()) if gid() else None
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 50)
    posts = (
        FeedPost.query.order_by(FeedPost.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "posts": [p.to_dict(viewer_id=viewer_id) for p in posts.items],
        "page": page, "has_more": posts.has_next,
    })


@feed_bp.route("", methods=["POST"])
@jwt_required()
def create_post():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required"}), 400
    link_url = (data.get("link") or {}).get("url", "")
    if link_url and not safe_url(link_url):
        return jsonify({"error": "link must start with http:// or https://"}), 400
    post = FeedPost(
        user_id=user_id, category=data.get("category", "Update"), content=content,
        tags_json=json.dumps(data.get("tags", [])),
        link_title=(data.get("link") or {}).get("title", ""),
        link_url=(data.get("link") or {}).get("url", ""),
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict(viewer_id=user_id)), 201


@feed_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    user_id = int(get_jwt_identity())
    post = FeedPost.query.filter_by(id=post_id, user_id=user_id).first_or_404()
    db.session.delete(post)
    db.session.commit()
    return jsonify({"status": "deleted"})


@feed_bp.route("/<int:post_id>/clap", methods=["POST"])
@jwt_required()
def toggle_clap(post_id):
    user_id = int(get_jwt_identity())
    post = FeedPost.query.get_or_404(post_id)
    existing = PostClap.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"hasClapped": False, "claps": post.claps.count()})
    db.session.add(PostClap(post_id=post_id, user_id=user_id))
    db.session.commit()
    return jsonify({"hasClapped": True, "claps": post.claps.count()})


@feed_bp.route("/<int:post_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(post_id):
    user_id = int(get_jwt_identity())
    FeedPost.query.get_or_404(post_id)
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    comment = Comment(post_id=post_id, user_id=user_id, text=text)
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201
