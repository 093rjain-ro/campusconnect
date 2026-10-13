import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory

try:
    from flask_cors import CORS
    has_cors = True
except ImportError:
    has_cors = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, ".db")
DB_PATH = os.path.join(DB_DIR, "campusconnect.db")

app = Flask(__name__, static_folder=BASE_DIR)
if has_cors:
    CORS(app)

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

# Ensure DB and tables exist on startup
import init_db
init_db.init_database()

# ─── STATIC FILES ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    if os.path.exists(os.path.join(BASE_DIR, filename)):
        return send_from_directory(BASE_DIR, filename)
    return jsonify({"error": "File not found"}), 404

# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.route("/api/status", methods=["GET"])
def api_status():
    """Returns database status and current table statistics."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        tables = [
            "ambassadors", "tasks", "task_completions", "daily_quests", 
            "quest_completions", "badges", "user_badges", "github_analyses",
            "placement_drives", "drive_applications", "drive_offers"
        ]
        counts = {}
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cursor.fetchone()[0]
            except Exception:
                counts[t] = 0
                
        conn.close()
        return jsonify({
            "status": "connected",
            "database_file": os.path.relpath(DB_PATH, BASE_DIR),
            "absolute_path": DB_PATH,
            "counts": counts
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/data", methods=["GET"])
def api_data():
    """Fetch initial data for the frontend."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Ambassadors
    cursor.execute("SELECT * FROM ambassadors ORDER BY points DESC")
    ambs = [dict(r) for r in cursor.fetchall()]
    
    # Tasks
    cursor.execute("SELECT * FROM tasks WHERE is_active = 1 ORDER BY id ASC")
    tasks = [dict(r) for r in cursor.fetchall()]
    
    # Quests
    cursor.execute("SELECT * FROM daily_quests ORDER BY id ASC")
    quests = [dict(r) for r in cursor.fetchall()]
    
    # Badges
    cursor.execute("SELECT * FROM badges ORDER BY id ASC")
    badges = [dict(r) for r in cursor.fetchall()]
    
    # Placement Drives (DBMS Project 22)
    cursor.execute("SELECT * FROM placement_drives ORDER BY drive_id DESC")
    drives = [dict(r) for r in cursor.fetchall()]
    
    # Applications
    cursor.execute("SELECT * FROM drive_applications ORDER BY app_id DESC")
    applications = [dict(r) for r in cursor.fetchall()]
    
    # Offers
    cursor.execute("SELECT * FROM drive_offers ORDER BY offer_id DESC")
    offers = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return jsonify({
        "ambassadors": ambs,
        "tasks": tasks,
        "dailyQuests": quests,
        "badges": badges,
        "placementDrives": drives,
        "applications": applications,
        "offers": offers
    })

@app.route("/api/ambassadors", methods=["POST"])
def add_or_update_ambassador():
    """Register or update an ambassador/student in SQLite."""
    data = request.json or {}
    name = data.get("name", "").strip()
    college = data.get("college", "Other").strip()
    avatar = data.get("avatar", "🦁")
    points = int(data.get("points", 100))
    streak = int(data.get("streak", 1))
    github_score = int(data.get("github_score", 0))
    role = data.get("role", "ambassador")

    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already exists
    cursor.execute("SELECT id, points FROM ambassadors WHERE LOWER(name) = LOWER(?)", (name,))
    existing = cursor.fetchone()
    if existing:
        user_id = existing["id"]
        cursor.execute("""
            UPDATE ambassadors 
            SET college = ?, avatar = ?, points = MAX(points, ?), streak = MAX(streak, ?), role = ?
            WHERE id = ?
        """, (college, avatar, points, streak, role, user_id))
    else:
        cursor.execute("""
            INSERT INTO ambassadors (name, college, avatar, points, streak, github_score, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, college, avatar, points, streak, github_score, role))
        user_id = cursor.lastrowid

    conn.commit()
    cursor.execute("SELECT * FROM ambassadors WHERE id = ?", (user_id,))
    amb = dict(cursor.fetchone())
    conn.close()
    
    return jsonify({"success": True, "ambassador": amb})

@app.route("/api/tasks", methods=["POST"])
def create_task():
    """Organization adds a new task to SQLite."""
    data = request.json or {}
    title = data.get("title", "").strip()
    pts = int(data.get("pts", 100))
    cat = data.get("cat", "Social").strip()
    description = data.get("description", "").strip()
    icon = data.get("icon", "📋")

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, pts, cat, description, icon)
        VALUES (?, ?, ?, ?, ?)
    """, (title, pts, cat, description, icon))
    conn.commit()
    task_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = dict(cursor.fetchone())
    conn.close()
    
    return jsonify({"success": True, "task": task})

@app.route("/api/tasks/complete", methods=["POST"])
def complete_task():
    """Record task completion and award XP in SQLite."""
    data = request.json or {}
    task_id = int(data.get("task_id", 0))
    user_name = data.get("user_name", "You").strip()
    points = int(data.get("points", 0))
    task_title = data.get("task_title", "")

    conn = get_db()
    cursor = conn.cursor()
    
    # Record completion
    cursor.execute("""
        INSERT INTO task_completions (user_name, task_id, task_title, points_earned)
        VALUES (?, ?, ?, ?)
    """, (user_name, task_id, task_title, points))
    
    # Update points for ambassador if user exists
    cursor.execute("""
        UPDATE ambassadors 
        SET points = points + ? 
        WHERE LOWER(name) = LOWER(?)
    """, (points, user_name))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "task_id": task_id, "points_earned": points})

@app.route("/api/quests/complete", methods=["POST"])
def complete_quest():
    """Record daily quest completion in SQLite."""
    data = request.json or {}
    quest_id = int(data.get("quest_id", 0))
    user_name = data.get("user_name", "You").strip()
    points = int(data.get("points", 50))
    quest_title = data.get("quest_title", "")

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO quest_completions (user_name, quest_id, quest_title, points_earned)
        VALUES (?, ?, ?, ?)
    """, (user_name, quest_id, quest_title, points))
    
    cursor.execute("""
        UPDATE ambassadors 
        SET points = points + ? 
        WHERE LOWER(name) = LOWER(?)
    """, (points, user_name))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "quest_id": quest_id, "points_earned": points})

@app.route("/api/github/save", methods=["POST"])
def save_github_analysis():
    """Save GitHub analyzer results to SQLite."""
    data = request.json or {}
    username = data.get("username", "").strip()
    score = int(data.get("score", 0))
    stars = int(data.get("stars", 0))
    repos = int(data.get("repos", 0))
    followers = int(data.get("followers", 0))
    verdict = data.get("verdict", "")
    ai_summary = data.get("ai_summary", "")
    user_name = data.get("user_name", "").strip()
    xp_gain = int(data.get("xp_gain", 0))

    if not username:
        return jsonify({"error": "GitHub username is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO github_analyses (username, score, stars, repos_count, followers, verdict, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, score, stars, repos, followers, verdict, ai_summary))
    
    if user_name:
        cursor.execute("""
            UPDATE ambassadors 
            SET github_score = ?, points = points + ? 
            WHERE LOWER(name) = LOWER(?)
        """, (score, xp_gain, user_name))
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "saved_analysis_for": username})

@app.route("/api/drives", methods=["POST"])
def create_drive():
    """Placement Officer creates a new recruitment drive in SQLite (DBMS Project 22)."""
    data = request.json or {}
    company = data.get("company_name", "").strip()
    role = data.get("job_role", "").strip()
    package_lpa = float(data.get("package_lpa", 0))
    min_cgpa = float(data.get("min_cgpa", 0))
    max_backlogs = int(data.get("max_backlogs", 0))
    branches = data.get("eligible_branches", "All branches").strip()
    drive_date = data.get("drive_date", "TBD").strip()

    if not company or not role:
        return jsonify({"error": "Company name and job role are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO placement_drives (company_name, job_role, package_lpa, min_cgpa, max_backlogs, eligible_branches, drive_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (company, role, package_lpa, min_cgpa, max_backlogs, branches, drive_date))
    conn.commit()
    drive_id = cursor.lastrowid
    conn.close()
    return jsonify({"success": True, "drive_id": drive_id})

@app.route("/api/applications", methods=["POST"])
def submit_application():
    """Student applies for a recruitment drive in SQLite (DBMS Project 22)."""
    data = request.json or {}
    student_name = data.get("student_name", "").strip()
    student_email = data.get("student_email", "").strip()
    drive_id = int(data.get("drive_id", 0))
    company_name = data.get("company_name", "").strip()
    job_role = data.get("job_role", "").strip()
    cgpa = float(data.get("cgpa", 8.0))

    if not student_name:
        return jsonify({"error": "Student name is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO drive_applications (student_name, student_email, drive_id, company_name, job_role, cgpa, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Applied')
    """, (student_name, student_email, drive_id, company_name, job_role, cgpa))
    conn.commit()
    app_id = cursor.lastrowid
    conn.close()
    return jsonify({"success": True, "app_id": app_id})

@app.route("/api/offers", methods=["POST"])
def issue_offer():
    """Issue a placement offer letter in SQLite (DBMS Project 22)."""
    data = request.json or {}
    student_name = data.get("student_name", "").strip()
    company_name = data.get("company_name", "").strip()
    job_role = data.get("job_role", "").strip()
    package_lpa = float(data.get("package_lpa", 0))

    if not student_name or not company_name:
        return jsonify({"error": "Student and company name are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO drive_offers (student_name, company_name, job_role, package_lpa, offer_status)
        VALUES (?, ?, ?, ?, 'Offered')
    """, (student_name, company_name, job_role, package_lpa))
    conn.commit()
    offer_id = cursor.lastrowid
    conn.close()
    return jsonify({"success": True, "offer_id": offer_id})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==========================================================")
    print(f"  CampusConnect SQLite Server Live!")
    print(f"  - Database: {DB_PATH}")
    print(f"  - View/Edit Live in DB Browser: {DB_PATH}")
    print(f"  - Web App URL: http://localhost:{port}")
    print(f"==========================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
