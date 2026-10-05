import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


def now():
    return datetime.utcnow()


def _loads(s, default):
    if not s:
        return default
    try:
        return json.loads(s)
    except (TypeError, ValueError):
        return default


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    avatar = db.Column(db.String(255), default="")
    cover_image = db.Column(db.String(255), default="")
    title = db.Column(db.String(200), default="")
    bio = db.Column(db.Text, default="")
    location = db.Column(db.String(120), default="")
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=250)
    next_level_xp = db.Column(db.Integer, default=1000)
    target_role_id = db.Column(db.String(50), default="fullstack-ai")
    open_for_peers = db.Column(db.Boolean, default=True)
    github = db.Column(db.String(200), default="")
    twitter = db.Column(db.String(200), default="")
    website = db.Column(db.String(200), default="")
    portfolio_enabled = db.Column(db.Boolean, default=False)
    portfolio_theme = db.Column(db.String(20), default="grape")
    created_at = db.Column(db.DateTime, default=now)

    skills = db.relationship("Skill", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    projects = db.relationship("Project", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_public_dict(self):
        """Lightweight shape used for peer lists / feed authorship."""
        return {
            "id": self.id, "name": self.name, "username": self.username,
            "avatar": self.avatar, "title": self.title, "level": self.level,
        }

    def to_dict(self, viewer_id=None):
        data = {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "avatar": self.avatar,
            "coverImage": self.cover_image,
            "title": self.title,
            "bio": self.bio,
            "location": self.location,
            "level": self.level,
            "xp": self.xp,
            "nextLevelXp": self.next_level_xp,
            "targetRoleId": self.target_role_id,
            "openForPeers": self.open_for_peers,
            "socials": {"github": self.github, "twitter": self.twitter, "website": self.website},
            "skills": [s.to_dict() for s in self.skills],
            "projects": [p.to_dict(viewer_id=viewer_id) for p in self.projects],
            "connectionsCount": connections_count(self.id),
            "portfolio": {
                "enabled": bool(self.portfolio_enabled),
                "theme": self.portfolio_theme or "grape",
                "path": f"/portfolio/{self.username}",
            },
        }
        # Email is private: only the account owner ever gets it back.
        if viewer_id is not None and viewer_id == self.id:
            data["email"] = self.email
        return data


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)
    category = db.Column(db.String(60), default="")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "score": self.score, "category": self.category}


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    tagline = db.Column(db.String(300), default="")
    description = db.Column(db.Text, default="")
    demo_url = db.Column(db.String(255), default="")
    repo_url = db.Column(db.String(255), default="")
    image = db.Column(db.String(255), default="")
    tags_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=now)

    claps = db.relationship("ProjectClap", backref="project", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, viewer_id=None):
        return {
            "id": self.id, "title": self.title, "tagline": self.tagline,
            "description": self.description, "demoUrl": self.demo_url, "repoUrl": self.repo_url,
            "image": self.image, "tags": _loads(self.tags_json, []),
            "createdAt": self.created_at.isoformat(),
            "claps": self.claps.count(),
            "hasClapped": (
                self.claps.filter_by(user_id=viewer_id).first() is not None if viewer_id else False
            ),
        }


class ProjectClap(db.Model):
    __tablename__ = "project_claps"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("project_id", "user_id", name="uq_project_clap"),)


class Connection(db.Model):
    """A connection request between two users. One row per pair: it starts as
    "pending" (requester -> addressee) and becomes "accepted" when the addressee
    accepts. Declined / cancelled / removed connections simply delete the row."""
    __tablename__ = "connections"
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending | accepted
    created_at = db.Column(db.DateTime, default=now)
    responded_at = db.Column(db.DateTime, nullable=True)

    requester = db.relationship("User", foreign_keys=[requester_id])
    addressee = db.relationship("User", foreign_keys=[addressee_id])


def connection_between(a_id, b_id):
    """The Connection row linking two users, in either direction (or None)."""
    return Connection.query.filter(
        db.or_(
            db.and_(Connection.requester_id == a_id, Connection.addressee_id == b_id),
            db.and_(Connection.requester_id == b_id, Connection.addressee_id == a_id),
        )
    ).first()


def connection_status(viewer_id, other_id):
    """self | none | pending_out | pending_in | connected  (from the viewer's side)."""
    if viewer_id is None:
        return "none"
    if viewer_id == other_id:
        return "self"
    c = connection_between(viewer_id, other_id)
    if not c:
        return "none"
    if c.status == "accepted":
        return "connected"
    return "pending_out" if c.requester_id == viewer_id else "pending_in"


def connections_count(user_id):
    return Connection.query.filter(
        Connection.status == "accepted",
        db.or_(Connection.requester_id == user_id, Connection.addressee_id == user_id),
    ).count()


class TargetRole(db.Model):
    __tablename__ = "target_roles"
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    market_salary_trend = db.Column(db.String(80), default="")
    growth_velocity = db.Column(db.String(80), default="")
    key_focus_json = db.Column(db.Text, default="[]")

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "marketSalaryTrend": self.market_salary_trend, "growthVelocity": self.growth_velocity,
            "keyFocus": _loads(self.key_focus_json, []),
        }


class RoadmapNode(db.Model):
    """Template node shared by every user working on a given role; per-user
    progress is tracked separately in UserNodeProgress."""
    __tablename__ = "roadmap_nodes"
    id = db.Column(db.String(50), primary_key=True)
    role_id = db.Column(db.String(50), db.ForeignKey("target_roles.id"), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), default="")
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=500)
    description = db.Column(db.Text, default="")
    why_in_2026 = db.Column(db.Text, default="")
    resources_json = db.Column(db.Text, default="[]")
    challenge = db.Column(db.Text, default="")
    circle_recommendation = db.Column(db.String(150), default="")
    default_status = db.Column(db.String(20), default="locked")

    def to_dict(self, user_id=None):
        status = self.default_status
        if user_id:
            progress = UserNodeProgress.query.filter_by(user_id=user_id, node_id=self.id).first()
            if progress:
                status = progress.status
        return {
            "id": self.id, "title": self.title, "category": self.category,
            "status": status, "level": self.level, "xp": self.xp,
            "description": self.description, "whyIn2026": self.why_in_2026,
            "resources": _loads(self.resources_json, []), "challenge": self.challenge,
            "circleRecommendation": self.circle_recommendation,
        }


class UserNodeProgress(db.Model):
    __tablename__ = "user_node_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    node_id = db.Column(db.String(50), db.ForeignKey("roadmap_nodes.id"), nullable=False)
    status = db.Column(db.String(20), default="in-progress")
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    __table_args__ = (db.UniqueConstraint("user_id", "node_id", name="uq_user_node"),)


class GrowthCircle(db.Model):
    __tablename__ = "growth_circles"
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    tagline = db.Column(db.String(300), default="")
    icon = db.Column(db.String(50), default="Sparkles")
    active_sprint = db.Column(db.String(200), default="")
    weekly_challenge = db.Column(db.Text, default="")
    tags_json = db.Column(db.Text, default="[]")

    memberships = db.relationship("CircleMembership", backref="circle", lazy="dynamic", cascade="all, delete-orphan")
    discussions = db.relationship("Discussion", backref="circle", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, user_id=None):
        return {
            "id": self.id, "name": self.name, "tagline": self.tagline, "icon": self.icon,
            "activeSprint": self.active_sprint, "weeklyChallenge": self.weekly_challenge,
            "tags": _loads(self.tags_json, []),
            "membersCount": self.memberships.count(),
            "isJoined": (
                self.memberships.filter_by(user_id=user_id).first() is not None if user_id else False
            ),
            "discussions": [d.to_dict() for d in self.discussions.order_by(Discussion.created_at.desc()).limit(10)],
        }


class CircleMembership(db.Model):
    __tablename__ = "circle_memberships"
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.String(50), db.ForeignKey("growth_circles.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("circle_id", "user_id", name="uq_circle_member"),)


class Discussion(db.Model):
    __tablename__ = "discussions"
    id = db.Column(db.Integer, primary_key=True)
    circle_id = db.Column(db.String(50), db.ForeignKey("growth_circles.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    author_name = db.Column(db.String(120), default="")  # for seeded/demo authors without a real account
    author_avatar = db.Column(db.String(255), default="")
    title = db.Column(db.String(300), nullable=False)
    replies_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        author = User.query.get(self.author_id) if self.author_id else None
        return {
            "id": self.id, "title": self.title, "repliesCount": self.replies_count,
            "time": timeago(self.created_at),
            "author": author.name if author else self.author_name,
            "avatar": author.avatar if author else self.author_avatar,
        }


class FeedPost(db.Model):
    __tablename__ = "feed_posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(60), default="Update")
    content = db.Column(db.Text, nullable=False)
    tags_json = db.Column(db.Text, default="[]")
    link_title = db.Column(db.String(200), default="")
    link_url = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=now)

    author = db.relationship("User")
    claps = db.relationship("PostClap", backref="post", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan",
                                order_by="Comment.created_at")

    def to_dict(self, viewer_id=None):
        data = {
            "id": self.id, "authorId": self.author.id,
            "authorName": self.author.name, "authorHandle": self.author.username,
            "authorAvatar": self.author.avatar, "authorTitle": self.author.title,
            "category": self.category, "content": self.content,
            "tags": _loads(self.tags_json, []),
            "timeAgo": timeago(self.created_at),
            "claps": self.claps.count(),
            "hasClapped": (
                self.claps.filter_by(user_id=viewer_id).first() is not None if viewer_id else False
            ),
            "comments": [c.to_dict() for c in self.comments],
        }
        if self.link_url:
            data["link"] = {"title": self.link_title, "url": self.link_url}
        return data


class PostClap(db.Model):
    __tablename__ = "post_claps"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("feed_posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="uq_post_clap"),)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("feed_posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now)

    author = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id, "authorId": self.author.id,
            "author": self.author.name, "avatar": self.author.avatar,
            "text": self.text, "timeAgo": timeago(self.created_at),
        }


class MarketTrend(db.Model):
    __tablename__ = "market_trends"
    id = db.Column(db.String(50), primary_key=True)
    skill = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), default="")
    demand_growth = db.Column(db.String(20), default="")
    status = db.Column(db.String(100), default="")
    description = db.Column(db.Text, default="")
    top_roles_json = db.Column(db.Text, default="[]")
    trend_score = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "skill": self.skill, "category": self.category,
            "demandGrowth": self.demand_growth, "status": self.status,
            "description": self.description, "topRoles": _loads(self.top_roles_json, []),
            "trendScore": self.trend_score,
        }


def timeago(dt):
    diff = (datetime.utcnow() - dt).total_seconds()
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{int(diff // 60)}m ago"
    if diff < 86400:
        return f"{int(diff // 3600)}h ago"
    if diff < 604800:
        return f"{int(diff // 86400)}d ago"
    return dt.strftime("%b %d")
