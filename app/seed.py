import json
from app import db
from app.models import (
    TargetRole, RoadmapNode, GrowthCircle, Discussion, MarketTrend, User, Skill, FeedPost
)

TARGET_ROLES = [
    dict(id="fullstack-ai", title="Full-Stack AI Engineer",
         description="Build end-to-end intelligent web applications powered by modern LLMs, vector search, and reactive interfaces.",
         market_salary_trend="$140k - $190k", growth_velocity="+42% demand in 2026",
         key_focus=["Vector DBs", "RAG Pipelines", "Next.js Server Actions", "TypeScript", "LangChain/LlamaIndex"]),
    dict(id="cloud-architect", title="Cloud Systems & DevOps Architect",
         description="Design resilient distributed infrastructure, Kubernetes clusters, zero-trust security, and CI/CD automation.",
         market_salary_trend="$150k - $210k", growth_velocity="+28% demand in 2026",
         key_focus=["Kubernetes", "Terraform", "Rust Infrastructure", "AWS/GCP Architecture", "eBPF Monitoring"]),
    dict(id="frontend-ux", title="UI/UX & Systems Frontend Specialist",
         description="Master modern web performance, design tokens, WebGL/canvas animation, and reactive state management.",
         market_salary_trend="$130k - $175k", growth_velocity="+35% demand in 2026",
         key_focus=["Design Systems", "WebGPU/Canvas", "Micro-frontends", "A11y Accessibility", "Framer Motion"]),
]

ROADMAP_NODES = [
    dict(id="node-1", role_id="fullstack-ai", order_index=1, title="Modern React & Server Components",
         category="Frontend Core", level=1, xp=400, default_status="mastered",
         description="Master React 19 Server Components, streaming SSR, and optimistic UI mutations.",
         why_in_2026="Standard foundation for high-performance AI web applications.",
         resources=[{"name": "React 19 Official Deep Dive", "url": "https://react.dev", "type": "Docs"},
                    {"name": "Server Actions & Streaming Patterns", "url": "https://nextjs.org/docs", "type": "Guide"}],
         challenge="Build a multi-step form with zero client JS overhead using Server Actions.",
         circle_recommendation="Frontend & Next.js Guild"),
    dict(id="node-2", role_id="fullstack-ai", order_index=2, title="Vector Embeddings & Semantic Search",
         category="AI Infrastructure", level=1, xp=600, default_status="mastered",
         description="Understand high-dimensional vector spaces, cosine similarity, Pinecone/pgvector, and hybrid search.",
         why_in_2026="Essential for contextual retrieval and modern RAG application intelligence.",
         resources=[{"name": "Vector Search Math & Practice", "url": "https://pinecone.io/learn", "type": "Interactive"},
                    {"name": "PGVector with PostgreSQL Cookbook", "url": "https://github.com/pgvector/pgvector", "type": "Code Repo"}],
         challenge="Implement a hybrid full-text + vector search API endpoint for markdown documents.",
         circle_recommendation="Generative AI Crafters"),
    dict(id="node-3", role_id="fullstack-ai", order_index=3, title="RAG Pipelines & Agent Tool Calling",
         category="AI Logic", level=2, xp=750, default_status="in-progress",
         description="Design autonomous AI agents capable of tool calls, structured outputs, and memory persistence.",
         why_in_2026="Enables interactive tools that go far beyond standard static chat boxes.",
         resources=[{"name": "Building AI Agents with LangChain", "url": "https://python.langchain.com", "type": "Course"},
                    {"name": "Vercel AI SDK 4.0 Walkthrough", "url": "https://sdk.vercel.ai", "type": "Tutorial"}],
         challenge="Build a coding assistant agent that can read git diffs and draft pull request summaries.",
         circle_recommendation="Generative AI Crafters"),
    dict(id="node-4", role_id="fullstack-ai", order_index=4, title="WebAssembly & Client-side Model Execution",
         category="Performance", level=2, xp=800, default_status="next",
         description="Run small LLMs and vector models directly inside the browser using ONNX Web & Wasm.",
         why_in_2026="Zero server cost AI features with 100% user privacy.",
         resources=[{"name": "Transformers.js Web Execution", "url": "https://huggingface.co/docs/transformers.js", "type": "Docs"},
                    {"name": "Rust to Wasm Compilation Guide", "url": "https://rustwasm.github.io", "type": "Guide"}],
         challenge="Compile a sentiment analysis model to Wasm and run inferences in under 10ms locally.",
         circle_recommendation="System Architecture & Rust Circle"),
    dict(id="node-5", role_id="fullstack-ai", order_index=5, title="Distributed Rate Limiting & Queue Workers",
         category="Backend Scale", level=3, xp=900, default_status="locked",
         description="Manage token usage limits, Redis sliding windows, and asynchronous background jobs for AI pipelines.",
         why_in_2026="Prevents runaway API costs and ensures zero drop in web responsiveness under heavy load.",
         resources=[{"name": "Upstash Redis Rate Limiting Patterns", "url": "https://upstash.com", "type": "Article"}],
         challenge="Construct a sliding window token bucket rate limiter with automatic exponential backoff.",
         circle_recommendation="System Architecture & Rust Circle"),
]

MARKET_TRENDS = [
    dict(id="tr-1", skill="Vector Databases & RAG", category="AI/ML", demand_growth="+58%",
         status="Hot Market Skill",
         description="Companies building internal AI tools need engineers proficient in vector indexing and hybrid search.",
         top_roles=["AI Engineer", "Full-Stack Developer", "Data Architect"], trend_score=96),
    dict(id="tr-2", skill="Rust & WebAssembly Systems", category="Systems & Web", demand_growth="+41%",
         status="Rising Rapidly",
         description="High performance web tools are migrating computational bottlenecks from JS to Rust Wasm modules.",
         top_roles=["Systems Developer", "Web Architect", "Security Engineer"], trend_score=89),
    dict(id="tr-3", skill="Next.js 15 & React Server Components", category="Frontend", demand_growth="+34%",
         status="Industry Standard",
         description="Dominant web stack for production scale applications with server-side streaming.",
         top_roles=["Frontend Engineer", "Full-Stack Dev"], trend_score=92),
    dict(id="tr-4", skill="eBPF & Cloud Native Observability", category="DevOps", demand_growth="+27%",
         status="High Value Specialty",
         description="Deep kernel-level telemetry and security monitoring without intrusive agent injection.",
         top_roles=["DevOps Engineer", "Site Reliability Engineer"], trend_score=81),
]

CIRCLES = [
    dict(id="circle-1", name="Generative AI & Agent Crafters",
         tagline="Exploring autonomous agents, local LLMs, and vector architecture together.",
         icon="BrainCircuit", active_sprint="Sprint #14: Build a Local Browser-Based RAG App",
         weekly_challenge="Implement function-calling using JSON Schema validation in your app.",
         tags=["LLMs", "Vector Search", "Python", "Wasm"]),
    dict(id="circle-2", name="System Architecture & Rust Circle",
         tagline="Mastering memory safety, concurrency patterns, and microservice optimization.",
         icon="Cpu", active_sprint="Sprint #9: Zero-Copy Async I/O Web Server in Rust",
         weekly_challenge="Refactor a synchronous file reader into a multi-threaded async worker queue.",
         tags=["Rust", "Systems", "Tokio", "Performance"]),
    dict(id="circle-3", name="UI Micro-Interactions & Motion Lab",
         tagline="Building fluid UI animations, glassmorphism design systems, and Canvas visualizers.",
         icon="Sparkles", active_sprint="Sprint #21: Interactive Data Visualizer with Canvas API",
         weekly_challenge="Create a 60fps particle background that responds to mouse hover velocity.",
         tags=["CSS Motion", "Framer Motion", "Canvas", "Design Tokens"]),
]

# A handful of demo peer accounts so the feed/peer list/matchmaker aren't empty
# on a fresh install. All use the password "password123" and are safe to delete
# in production seeding.
DEMO_PEERS = [
    dict(email="maya@example.com", username="mayalin_cloud", name="Maya Lin",
         title="Cloud Architect & Infrastructure Dev",
         avatar="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&auto=format&fit=crop&q=80",
         level=16, target_role_id="cloud-architect",
         skills=[("Kubernetes", 90, "DevOps"), ("Rust", 78, "Systems"), ("System Architecture", 85, "Architecture")]),
    dict(email="liam@example.com", username="liam_vance", name="Liam Vance",
         title="AI Researcher & ML Engineer",
         avatar="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
         level=15, target_role_id="fullstack-ai",
         skills=[("PyTorch", 88, "AI/ML"), ("RAG Pipelines", 82, "AI/ML"), ("Vector Search", 80, "AI/ML")]),
    dict(email="devon@example.com", username="devon_rust", name="Devon Cole",
         title="Rust Systems Engineer",
         avatar="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&auto=format&fit=crop&q=80",
         level=13, target_role_id="cloud-architect",
         skills=[("Rust", 92, "Systems"), ("WebAssembly", 75, "Performance"), ("Async I/O", 80, "Systems")]),
]

DEMO_POSTS = [
    dict(author_email="maya@example.com", category="Project Showcase",
         content="Just published my peer project: KubePulse - an open-source visual dashboard for monitoring "
                 "microservice health using eBPF telemetry! Looking for peer feedback on the topology graph view.",
         tags=["Kubernetes", "eBPF", "React", "Go"],
         link_title="KubePulse GitHub Repo", link_url="https://github.com/mayalin/kubepulse"),
    dict(author_email="devon@example.com", category="Skill Milestone",
         content="Leveling up in the Full-Stack AI Path! Just passed the 'Vector Search Math & Hybrid Ranking' "
                 "node. Check out my benchmark notebook comparing HNSW vs IVF indexing.",
         tags=["Skill Milestone", "Vector Search", "Rust"]),
    dict(author_email="liam@example.com", category="Peer Match Request",
         content="Peer Collaboration Wanted: Building an open-source accessibility contrast analyzer for "
                 "Figma tokens. Need a Frontend/Wasm peer to help optimize the color matrix calculations!",
         tags=["Pair Learning", "UI/UX", "Wasm"]),
]


def run_seed():
    if TargetRole.query.first():
        return  # already seeded

    for r in TARGET_ROLES:
        db.session.add(TargetRole(
            id=r["id"], title=r["title"], description=r["description"],
            market_salary_trend=r["market_salary_trend"], growth_velocity=r["growth_velocity"],
            key_focus_json=json.dumps(r["key_focus"]),
        ))

    for n in ROADMAP_NODES:
        db.session.add(RoadmapNode(
            id=n["id"], role_id=n["role_id"], order_index=n["order_index"], title=n["title"],
            category=n["category"], level=n["level"], xp=n["xp"], default_status=n["default_status"],
            description=n["description"], why_in_2026=n["why_in_2026"],
            resources_json=json.dumps(n["resources"]), challenge=n["challenge"],
            circle_recommendation=n["circle_recommendation"],
        ))

    for t in MARKET_TRENDS:
        db.session.add(MarketTrend(
            id=t["id"], skill=t["skill"], category=t["category"], demand_growth=t["demand_growth"],
            status=t["status"], description=t["description"],
            top_roles_json=json.dumps(t["top_roles"]), trend_score=t["trend_score"],
        ))

    for c in CIRCLES:
        db.session.add(GrowthCircle(
            id=c["id"], name=c["name"], tagline=c["tagline"], icon=c["icon"],
            active_sprint=c["active_sprint"], weekly_challenge=c["weekly_challenge"],
            tags_json=json.dumps(c["tags"]),
        ))
    db.session.flush()

    db.session.add(Discussion(circle_id="circle-1", author_name="Maya Lin",
                               author_avatar=DEMO_PEERS[0]["avatar"],
                               title="Benchmark results: ONNX Web vs WebGPU for local embeddings",
                               replies_count=14))
    db.session.add(Discussion(circle_id="circle-2", author_name="Devon Cole",
                               author_avatar=DEMO_PEERS[2]["avatar"],
                               title="Understanding Tokio task cancellation safety rules",
                               replies_count=22))

    peer_objs = {}
    for p in DEMO_PEERS:
        user = User(
            email=p["email"], username=p["username"], name=p["name"], title=p["title"],
            avatar=p["avatar"], level=p["level"], xp=p["level"] * 500,
            next_level_xp=(p["level"] + 1) * 500, target_role_id=p["target_role_id"],
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()
        for name, score, category in p["skills"]:
            db.session.add(Skill(user_id=user.id, name=name, score=score, category=category))
        peer_objs[p["email"]] = user

    db.session.flush()

    for post in DEMO_POSTS:
        author = peer_objs[post["author_email"]]
        db.session.add(FeedPost(
            user_id=author.id, category=post["category"], content=post["content"],
            tags_json=json.dumps(post["tags"]),
            link_title=post.get("link_title", ""), link_url=post.get("link_url", ""),
        ))

    db.session.commit()
