import sqlite3, os, hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'cybershield.db')

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_conn()
    conn.cursor().execute('''CREATE TABLE IF NOT EXISTS attack_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, src_ip TEXT, dst_ip TEXT,
        protocol TEXT, port INTEGER, attack_type TEXT,
        risk_score INTEGER, risk_level TEXT,
        confidence REAL, top_reason TEXT,
        packet_count INTEGER, src_bytes INTEGER, dst_bytes INTEGER)''')
    # ── Users Table ──
    conn.cursor().execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT)''')
    conn.commit(); conn.close()

def register_user(username, password):
    """Naya user register karo. Returns True agar success, False agar username already exists."""
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                  (username, hash_password(password),
                   datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit(); conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists

def verify_user(username, password):
    """Login verify karo. Returns True agar credentials sahi hain."""
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row['password'] == hash_password(password):
        return True
    return False

def insert_log(d):
    conn = get_conn(); c = conn.cursor()
    c.execute('''INSERT INTO attack_logs
        (timestamp,src_ip,dst_ip,protocol,port,attack_type,
         risk_score,risk_level,confidence,top_reason,packet_count,src_bytes,dst_bytes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        d.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        d.get('src_ip','0.0.0.0'), d.get('dst_ip','0.0.0.0'),
        d.get('protocol','TCP'), d.get('port',80),
        d.get('attack_type','unknown'), d.get('risk_score',0),
        d.get('risk_level','LOW'), d.get('confidence',0.0),
        d.get('top_reason',''), d.get('packet_count',0),
        d.get('src_bytes',0), d.get('dst_bytes',0)))
    conn.commit(); conn.close()

def get_recent_logs(limit=50):
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT * FROM attack_logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close(); return rows

def get_stats():
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT COUNT(*) as total FROM attack_logs')
    total = c.fetchone()['total']
    c.execute("SELECT COUNT(*) as a FROM attack_logs WHERE attack_type!='normal'")
    attacks = c.fetchone()['a']
    c.execute("SELECT COUNT(*) as h FROM attack_logs WHERE risk_level='HIGH'")
    high = c.fetchone()['h']
    c.execute('SELECT attack_type, COUNT(*) as count FROM attack_logs GROUP BY attack_type ORDER BY count DESC')
    by_type = [dict(r) for r in c.fetchall()]
    c.execute("SELECT strftime('%H',timestamp) as hour, COUNT(*) as count FROM attack_logs GROUP BY hour")
    by_hour = [dict(r) for r in c.fetchall()]
    conn.close()
    return {'total':total,'attacks':attacks,'high_risk':high,
            'normal':total-attacks,'by_type':by_type,'by_hour':by_hour}

def get_all_logs():
    conn = get_conn(); c = conn.cursor()
    c.execute('SELECT * FROM attack_logs ORDER BY id DESC')
    rows = [dict(r) for r in c.fetchall()]
    conn.close(); return rows
