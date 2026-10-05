import json
import re
from flask import Blueprint, render_template, abort
from app.models import User, Project
from app.utils import safe_url

portfolio_bp = Blueprint("portfolio", __name__)

THEMES = {
    "grape":  ("#6B4DFF", "#FF4F8B"),
    "sunset": ("#FF8A3D", "#FF4F8B"),
    "mint":   ("#10BF8A", "#38BDF8"),
    "sky":    ("#38BDF8", "#6B4DFF"),
}
HANDLE = re.compile(r"^@?([A-Za-z0-9_.-]{1,60})$")


def social_url(kind, value):
    """Socials are free text: accept a full URL or just a handle."""
    v = (value or "").strip()
    if not v:
        return ""
    if safe_url(v):
        return v
    m = HANDLE.match(v)
    if m and kind in ("github", "twitter"):
        host = "github.com" if kind == "github" else "x.com"
        return f"https://{host}/{m.group(1)}"
    if kind == "website" and re.match(r"^[\w.-]+\.[A-Za-z]{2,}(/\S*)?$", v):
        return "https://" + v
    return ""


@portfolio_bp.route("/<username>")
def show_portfolio(username):
    user = User.query.filter_by(username=username.lower()).first()
    if not user or not user.portfolio_enabled:
        abort(404)
    c1, c2 = THEMES.get(user.portfolio_theme, THEMES["grape"])
    socials = [(label, social_url(kind, val)) for label, kind, val in (
        ("GitHub", "github", user.github), ("Twitter / X", "twitter", user.twitter),
        ("Website", "website", user.website))]
    projects = [{
        "title": p.title, "tagline": p.tagline, "description": p.description,
        "image": safe_url(p.image), "demo": safe_url(p.demo_url), "repo": safe_url(p.repo_url),
        "tags": json.loads(p.tags_json or "[]"), "claps": p.claps.count(),
    } for p in user.projects.order_by(Project.created_at.desc()).all()]
    skills = sorted(user.skills, key=lambda s: s.score, reverse=True)
    return render_template(
        "portfolio.html", u=user, c1=c1, c2=c2, avatar=safe_url(user.avatar),
        socials=[s for s in socials if s[1]], projects=projects, skills=skills,
    )


@portfolio_bp.app_errorhandler(404)
def not_found(e):
    from flask import request, jsonify
    if request.path.startswith("/portfolio/"):
        return render_template("portfolio_404.html"), 404
    if request.path.startswith("/api/"):
        return jsonify({"error": "not found"}), 404
    return e
