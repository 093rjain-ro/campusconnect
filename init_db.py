import os
import sqlite3

DB_DIR = os.path.join(os.path.dirname(__file__), ".db")
DB_PATH = os.path.join(DB_DIR, "campusconnect.db")

def init_database():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. Ambassadors / Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ambassadors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        college TEXT NOT NULL,
        avatar TEXT DEFAULT '🦁',
        points INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        github_score INTEGER DEFAULT 0,
        role TEXT DEFAULT 'ambassador',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        pts INTEGER NOT NULL,
        cat TEXT NOT NULL,
        description TEXT,
        icon TEXT DEFAULT '📋',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Task Completions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS task_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,
        task_id INTEGER,
        task_title TEXT,
        points_earned INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    );
    """)

    # 4. Daily Quests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        pts INTEGER NOT NULL,
        icon TEXT DEFAULT '⭐',
        action TEXT
    );
    """)

    # 5. Daily Quest Completions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        quest_id INTEGER,
        quest_title TEXT,
        points_earned INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (quest_id) REFERENCES daily_quests (id)
    );
    """)

    # 6. Badges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT,
        pts INTEGER DEFAULT 100
    );
    """)

    # 7. User Badges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        badge_name TEXT,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. GitHub Analyses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        score INTEGER NOT NULL,
        stars INTEGER DEFAULT 0,
        repos_count INTEGER DEFAULT 0,
        followers INTEGER DEFAULT 0,
        verdict TEXT,
        ai_summary TEXT,
        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. DBMS Project 22 - Placement Drives
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS placement_drives (
        drive_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        job_role TEXT NOT NULL,
        package_lpa REAL NOT NULL,
        min_cgpa REAL NOT NULL,
        max_backlogs INTEGER DEFAULT 0,
        eligible_branches TEXT DEFAULT 'All branches',
        drive_date TEXT,
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 10. DBMS Project 22 - Drive Applications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drive_applications (
        app_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        student_email TEXT,
        drive_id INTEGER,
        company_name TEXT,
        job_role TEXT,
        cgpa REAL,
        status TEXT DEFAULT 'Applied',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (drive_id) REFERENCES placement_drives (drive_id)
    );
    """)

    # 11. DBMS Project 22 - Drive Round Results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drive_round_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER,
        student_name TEXT,
        round_name TEXT,
        status TEXT,
        remarks TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (app_id) REFERENCES drive_applications (app_id)
    );
    """)

    # 12. DBMS Project 22 - Drive Offers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drive_offers (
        offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        company_name TEXT NOT NULL,
        job_role TEXT NOT NULL,
        package_lpa REAL NOT NULL,
        offer_status TEXT DEFAULT 'Offered',
        issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # --- SEED INITIAL DATA IF EMPTY ---
    # Seed Ambassadors
    cursor.execute("SELECT COUNT(*) FROM ambassadors;")
    if cursor.fetchone()[0] == 0:
        ambassadors = [
            ("Arjun Sharma", "IIT Delhi", "🦁", 4250, 21, 87, "ambassador"),
            ("Priya Nair", "NIT Trichy", "🦋", 3890, 14, 79, "ambassador"),
            ("Rahul Gupta", "BITS Pilani", "🐺", 3200, 7, 72, "ambassador"),
            ("Sneha Roy", "VIT Vellore", "🦊", 2850, 5, 65, "ambassador"),
            ("Vikram Singh", "IIIT Hyderabad", "🐻", 2100, 3, 58, "ambassador"),
            ("Ananya K", "Osmania University", "🐯", 1950, 0, 52, "ambassador")
        ]
        cursor.executemany("""
        INSERT INTO ambassadors (name, college, avatar, points, streak, github_score, role)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, ambassadors)

    # Seed Tasks
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    if cursor.fetchone()[0] == 0:
        tasks = [
            ("Share UnsaidTalks on LinkedIn", 150, "Social", "Post about UnsaidTalks and tag 3 friends", "📢"),
            ("Refer 3 college friends to sign up", 300, "Referral", "Get 3 friends to register using your referral code", "🎯"),
            ("Host a campus session (20+ attendees)", 500, "Event", "Organize and lead a campus-level workshop or session", "🎤"),
            ("Improve your GitHub README", 100, "GitHub", "Add a comprehensive README to your top repository", "💻"),
            ("Submit a video testimonial", 200, "Content", "Record a 60-second testimonial about your experience", "🎬"),
            ("Create an Instagram reel", 250, "Content", "Showcase UnsaidTalks in a creative 30-second reel", "📸"),
            ("Post about your CA journey", 100, "Social", "Share your ambassador experience publicly", "📱"),
            ("Engage with 5 UnsaidTalks posts", 50, "Social", "Like, comment, and share 5 official posts this week", "💬")
        ]
        cursor.executemany("""
        INSERT INTO tasks (title, pts, cat, description, icon)
        VALUES (?, ?, ?, ?, ?);
        """, tasks)

    # Seed Daily Quests
    cursor.execute("SELECT COUNT(*) FROM daily_quests;")
    if cursor.fetchone()[0] == 0:
        quests = [
            ("Daily check-in completed", 50, "✅", "checkin"),
            ("Analyze a GitHub profile", 100, "⭐", "github"),
            ("Share CampusConnect with a friend", 75, "🎯", "tasks")
        ]
        cursor.executemany("""
        INSERT INTO daily_quests (title, pts, icon, action)
        VALUES (?, ?, ?, ?);
        """, quests)

    # Seed Badges
    cursor.execute("SELECT COUNT(*) FROM badges;")
    if cursor.fetchone()[0] == 0:
        badges = [
            ("GitHub Star", "Score 70+ on GitHub analysis", "⭐", 200),
            ("Week Warrior", "Maintain a 7-day active streak", "🔥", 300),
            ("Social Pro", "Complete all 3 social tasks", "📢", 150),
            ("Referral King", "10 successful referrals", "🎯", 500),
            ("Event Host", "Host a campus session", "🎤", 400),
            ("Content Creator", "Submit 3 content pieces", "🎬", 250),
            ("Top 10", "Reach leaderboard top 10", "🏆", 100),
            ("Legend", "Reach 5000 total XP", "👑", 1000)
        ]
        cursor.executemany("""
        INSERT INTO badges (name, description, icon, pts)
        VALUES (?, ?, ?, ?);
        """, badges)

    # Seed Placement Drives (DBMS Project 22)
    cursor.execute("SELECT COUNT(*) FROM placement_drives;")
    if cursor.fetchone()[0] == 0:
        drives = [
            ("Google Cloud", "Cloud Solutions Architect", 22.5, 8.5, 0, "CSE, IT, ECE", "2026-10-25", "Active"),
            ("Microsoft", "Software Development Engineer", 24.0, 8.0, 0, "CSE, IT", "2026-10-30", "Active"),
            ("Amazon AWS", "DevOps Engineer", 18.0, 7.5, 1, "All branches", "2026-11-05", "Active"),
            ("Goldman Sachs", "Analyst - Technology", 21.0, 8.0, 0, "CSE, IT, ECE, EEE", "2026-11-12", "Active")
        ]
        cursor.executemany("""
        INSERT INTO placement_drives (company_name, job_role, package_lpa, min_cgpa, max_backlogs, eligible_branches, drive_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, drives)

    # Seed Sample Applications & Offers
    cursor.execute("SELECT COUNT(*) FROM drive_applications;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO drive_applications (student_name, student_email, drive_id, company_name, job_role, cgpa, status)
        VALUES ('Arjun Sharma', 'arjun@iitd.ac.in', 1, 'Google Cloud', 'Cloud Solutions Architect', 9.1, 'Shortlisted');
        """)
        cursor.execute("""
        INSERT INTO drive_offers (student_name, company_name, job_role, package_lpa, offer_status)
        VALUES ('Arjun Sharma', 'Google Cloud', 'Cloud Solutions Architect', 22.5, 'Offered');
        """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized successfully at: {DB_PATH}")

if __name__ == "__main__":
    init_database()
