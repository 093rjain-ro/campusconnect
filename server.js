const http = require('http');
const fs = require('fs');
const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const BASE_DIR = __dirname;
const DB_DIR = path.join(BASE_DIR, '.db');
const DB_PATH = path.join(DB_DIR, 'campusconnect.db');

if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

// Connect to SQLite database in .db/campusconnect.db
const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA journal_mode = WAL;');
db.exec('PRAGMA foreign_keys = ON;');

// Initialize tables if needed
db.exec(`
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

CREATE TABLE IF NOT EXISTS daily_quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    pts INTEGER NOT NULL,
    icon TEXT DEFAULT '⭐',
    action TEXT
);

CREATE TABLE IF NOT EXISTS quest_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    quest_id INTEGER,
    quest_title TEXT,
    points_earned INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quest_id) REFERENCES daily_quests (id)
);

CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    pts INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS user_badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT,
    badge_name TEXT,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS drive_applications (
    app_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    student_email TEXT,
    drive_id INTEGER,
    company_name TEXT,
    job_role TEXT,
    cgpa REAL,
    status TEXT DEFAULT 'Applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drive_offers (
    offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    company_name TEXT NOT NULL,
    job_role TEXT NOT NULL,
    package_lpa REAL NOT NULL,
    offer_status TEXT DEFAULT 'Offered',
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
`);

function sendJSON(res, data, statusCode = 200) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(JSON.stringify(data));
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (e) {
        resolve({});
      }
    });
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  // CORS Preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    return res.end();
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;

  // ─── API ROUTES ───
  if (pathname === '/api/status' && req.method === 'GET') {
    const tables = ['ambassadors', 'tasks', 'task_completions', 'daily_quests', 'badges', 'github_analyses', 'placement_drives', 'drive_applications', 'drive_offers'];
    const counts = {};
    for (const t of tables) {
      try {
        const row = db.prepare(`SELECT COUNT(*) as c FROM ${t}`).get();
        counts[t] = row.c;
      } catch (e) {
        counts[t] = 0;
      }
    }
    return sendJSON(res, {
      status: 'connected',
      database_file: path.relative(BASE_DIR, DB_PATH),
      absolute_path: DB_PATH,
      counts
    });
  }

  if (pathname === '/api/data' && req.method === 'GET') {
    const ambassadors = db.prepare('SELECT * FROM ambassadors ORDER BY points DESC').all();
    const tasks = db.prepare('SELECT * FROM tasks WHERE is_active = 1 ORDER BY id ASC').all();
    const dailyQuests = db.prepare('SELECT * FROM daily_quests ORDER BY id ASC').all();
    const badges = db.prepare('SELECT * FROM badges ORDER BY id ASC').all();
    const placementDrives = db.prepare('SELECT * FROM placement_drives ORDER BY drive_id DESC').all();
    const applications = db.prepare('SELECT * FROM drive_applications ORDER BY app_id DESC').all();
    const offers = db.prepare('SELECT * FROM drive_offers ORDER BY offer_id DESC').all();

    return sendJSON(res, {
      ambassadors, tasks, dailyQuests, badges, placementDrives, applications, offers
    });
  }

  if (pathname === '/api/ambassadors' && req.method === 'POST') {
    const data = await parseBody(req);
    const name = (data.name || '').trim();
    const college = (data.college || 'Other').trim();
    const avatar = data.avatar || '🦁';
    const points = parseInt(data.points || 100);
    const streak = parseInt(data.streak || 1);
    const githubScore = parseInt(data.github_score || 0);
    const role = data.role || 'ambassador';

    if (!name) return sendJSON(res, { error: 'Name required' }, 400);

    const existing = db.prepare('SELECT id FROM ambassadors WHERE LOWER(name) = LOWER(?)').get(name);
    let userId;
    if (existing) {
      userId = existing.id;
      db.prepare(`UPDATE ambassadors SET college = ?, avatar = ?, points = MAX(points, ?), streak = MAX(streak, ?), role = ? WHERE id = ?`)
        .run(college, avatar, points, streak, role, userId);
    } else {
      const stmt = db.prepare(`INSERT INTO ambassadors (name, college, avatar, points, streak, github_score, role) VALUES (?, ?, ?, ?, ?, ?, ?)`);
      const info = stmt.run(name, college, avatar, points, streak, githubScore, role);
      userId = info.lastInsertRowid;
    }

    const amb = db.prepare('SELECT * FROM ambassadors WHERE id = ?').get(userId);
    return sendJSON(res, { success: true, ambassador: amb });
  }

  if (pathname === '/api/tasks' && req.method === 'POST') {
    const data = await parseBody(req);
    const title = (data.title || '').trim();
    const pts = parseInt(data.pts || 100);
    const cat = (data.cat || 'Social').trim();
    const description = (data.description || '').trim();
    const icon = data.icon || '📋';

    if (!title) return sendJSON(res, { error: 'Title required' }, 400);

    const stmt = db.prepare(`INSERT INTO tasks (title, pts, cat, description, icon) VALUES (?, ?, ?, ?, ?)`);
    const info = stmt.run(title, pts, cat, description, icon);
    const task = db.prepare('SELECT * FROM tasks WHERE id = ?').get(info.lastInsertRowid);
    return sendJSON(res, { success: true, task });
  }

  if (pathname === '/api/tasks/complete' && req.method === 'POST') {
    const data = await parseBody(req);
    const taskId = parseInt(data.task_id || 0);
    const userName = (data.user_name || 'You').trim();
    const points = parseInt(data.points || 0);
    const taskTitle = data.task_title || '';

    db.prepare(`INSERT INTO task_completions (user_name, task_id, task_title, points_earned) VALUES (?, ?, ?, ?)`).run(userName, taskId, taskTitle, points);
    db.prepare(`UPDATE ambassadors SET points = points + ? WHERE LOWER(name) = LOWER(?)`).run(points, userName);
    return sendJSON(res, { success: true, points_earned: points });
  }

  if (pathname === '/api/quests/complete' && req.method === 'POST') {
    const data = await parseBody(req);
    const questId = parseInt(data.quest_id || 0);
    const userName = (data.user_name || 'You').trim();
    const points = parseInt(data.points || 50);
    const questTitle = data.quest_title || '';

    db.prepare(`INSERT INTO quest_completions (user_name, quest_id, quest_title, points_earned) VALUES (?, ?, ?, ?)`).run(userName, questId, questTitle, points);
    db.prepare(`UPDATE ambassadors SET points = points + ? WHERE LOWER(name) = LOWER(?)`).run(points, userName);
    return sendJSON(res, { success: true, points_earned: points });
  }

  if (pathname === '/api/github/save' && req.method === 'POST') {
    const data = await parseBody(req);
    const username = (data.username || '').trim();
    const score = parseInt(data.score || 0);
    const stars = parseInt(data.stars || 0);
    const repos = parseInt(data.repos || 0);
    const followers = parseInt(data.followers || 0);
    const verdict = data.verdict || '';
    const aiSummary = data.ai_summary || '';
    const userName = (data.user_name || '').trim();
    const xpGain = parseInt(data.xp_gain || 0);

    if (!username) return sendJSON(res, { error: 'Username required' }, 400);

    db.prepare(`INSERT INTO github_analyses (username, score, stars, repos_count, followers, verdict, ai_summary) VALUES (?, ?, ?, ?, ?, ?, ?)`).run(username, score, stars, repos, followers, verdict, aiSummary);

    if (userName) {
      db.prepare(`UPDATE ambassadors SET github_score = ?, points = points + ? WHERE LOWER(name) = LOWER(?)`).run(score, xpGain, userName);
    }
    return sendJSON(res, { success: true, saved_analysis_for: username });
  }

  if (pathname === '/api/drives' && req.method === 'POST') {
    const data = await parseBody(req);
    const company = (data.company_name || '').trim();
    const role = (data.job_role || '').trim();
    const packageLpa = parseFloat(data.package_lpa || 0);
    const minCgpa = parseFloat(data.min_cgpa || 0);
    const maxBacklogs = parseInt(data.max_backlogs || 0);
    const branches = (data.eligible_branches || 'All branches').trim();
    const driveDate = (data.drive_date || 'TBD').trim();

    if (!company || !role) return sendJSON(res, { error: 'Company and role required' }, 400);

    const stmt = db.prepare(`INSERT INTO placement_drives (company_name, job_role, package_lpa, min_cgpa, max_backlogs, eligible_branches, drive_date) VALUES (?, ?, ?, ?, ?, ?, ?)`);
    const info = stmt.run(company, role, packageLpa, minCgpa, maxBacklogs, branches, driveDate);
    return sendJSON(res, { success: true, drive_id: Number(info.lastInsertRowid) });
  }

  if (pathname === '/api/applications' && req.method === 'POST') {
    const data = await parseBody(req);
    const studentName = (data.student_name || '').trim();
    const studentEmail = (data.student_email || '').trim();
    const driveId = parseInt(data.drive_id || 0);
    const companyName = (data.company_name || '').trim();
    const jobRole = (data.job_role || '').trim();
    const cgpa = parseFloat(data.cgpa || 8.0);

    if (!studentName) return sendJSON(res, { error: 'Student name required' }, 400);

    const stmt = db.prepare(`INSERT INTO drive_applications (student_name, student_email, drive_id, company_name, job_role, cgpa, status) VALUES (?, ?, ?, ?, ?, ?, 'Applied')`);
    const info = stmt.run(studentName, studentEmail, driveId, companyName, jobRole, cgpa);
    return sendJSON(res, { success: true, app_id: Number(info.lastInsertRowid) });
  }

  if (pathname === '/api/offers' && req.method === 'POST') {
    const data = await parseBody(req);
    const studentName = (data.student_name || '').trim();
    const companyName = (data.company_name || '').trim();
    const jobRole = (data.job_role || '').trim();
    const packageLpa = parseFloat(data.package_lpa || 0);

    if (!studentName || !companyName) return sendJSON(res, { error: 'Student and company required' }, 400);

    const stmt = db.prepare(`INSERT INTO drive_offers (student_name, company_name, job_role, package_lpa, offer_status) VALUES (?, ?, ?, ?, 'Offered')`);
    const info = stmt.run(studentName, companyName, jobRole, packageLpa);
    return sendJSON(res, { success: true, offer_id: Number(info.lastInsertRowid) });
  }

  // ─── STATIC FILE SERVING ───
  let filePath = pathname === '/' ? path.join(BASE_DIR, 'index.html') : path.join(BASE_DIR, pathname);
  
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      '.html': 'text/html; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.svg': 'image/svg+xml',
      '.json': 'application/json'
    };
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('404 Not Found');
  }
});

const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`\n==========================================================`);
  console.log(`  CampusConnect Node.js SQLite Server Live!`);
  console.log(`  - Database: ${DB_PATH}`);
  console.log(`  - View/Edit Live in DB Browser: ${DB_PATH}`);
  console.log(`  - Web App URL: http://localhost:${PORT}`);
  console.log(`==========================================================\n`);
});
