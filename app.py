# app.py — poora replace karo
# app.py ke bilkul upar add karo
import os
os.makedirs('model', exist_ok=True)
os.makedirs('database', exist_ok=True)
os.makedirs('static', exist_ok=True)
from flask import (Flask, render_template, jsonify, request,
                   send_file, redirect, url_for, session, flash)
from flask_mail import Mail
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from datetime import datetime
from functools import wraps
import threading, time, os

from config import Config
from utils.detector import simulate_packet, predict, load_model
from utils.db_utils  import (init_db, insert_log, get_recent_logs,
                              get_stats, get_all_logs)
from utils.pdf_generator import generate_report
from utils.alert_manager import (send_email_alert, send_telegram_alert,
                                  get_geoip)

# ── App Setup ────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

# ── FIX: Render pe Gunicorn use hota hai isliye yahan call karo ──
init_db()
load_model()
# ─────────────────────────────────────────────────────────────────

mail         = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

# ── Simple Admin User ────────────────────────────────────
class AdminUser(UserMixin):
    def __init__(self):
        self.id = 'admin'

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return AdminUser()
    return None

# ── Global State ─────────────────────────────────────────
monitoring_active = False
monitor_thread    = None
latest_alerts     = []
geo_cache         = {}   # ip → geo data cache

# ── Background Monitor ───────────────────────────────────
def monitor_loop():
    global monitoring_active, latest_alerts
    while monitoring_active:
        try:
            pkt    = simulate_packet()
            result = predict(pkt)
            insert_log(result)

            # GeoIP cache
            ip = result.get('src_ip','')
            if ip not in geo_cache:
                geo_cache[ip] = get_geoip(ip)
            result['geo'] = geo_cache[ip]

            if result['risk_level'] in ('HIGH','MEDIUM') and result['attack_type'] != 'normal':
                latest_alerts = (latest_alerts + [result])[-20:]

                # Send alerts only for HIGH risk
                if result['risk_level'] == 'HIGH':
                    threading.Thread(
                        target=send_email_alert,
                        args=(app, mail, result),
                        daemon=True
                    ).start()
                    threading.Thread(
                        target=send_telegram_alert,
                        args=(app.config['TELEGRAM_BOT_TOKEN'],
                              app.config['TELEGRAM_CHAT_ID'], result),
                        daemon=True
                    ).start()
            time.sleep(1.5)
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(2)

# ── Auth Routes ──────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','')
        password = request.form.get('password','')
        if (username == app.config['ADMIN_USERNAME'] and
                password == app.config['ADMIN_PASSWORD']):
            login_user(AdminUser(), remember=True)
            return redirect(url_for('dashboard'))
        flash('❌ Wrong username or password!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

# ── Main Routes (Protected) ──────────────────────────────
@app.route('/')
@login_required
def dashboard(): return render_template('dashboard.html')

@app.route('/analysis')
@login_required
def analysis(): return render_template('analysis.html')

@app.route('/alerts')
@login_required
def alerts_page(): return render_template('alerts.html')

@app.route('/risk')
@login_required
def risk_page(): return render_template('risk.html')

@app.route('/xai')
@login_required
def xai_page(): return render_template('xai.html')

@app.route('/reports')
@login_required
def reports_page(): return render_template('reports.html')

@app.route('/geomap')
@login_required
def geomap_page(): return render_template('geomap.html')

# ── API Endpoints ─────────────────────────────────────────
@app.route('/api/stats')
@login_required
def api_stats(): return jsonify(get_stats())

@app.route('/api/logs')
@login_required
def api_logs():
    limit = request.args.get('limit', 50, type=int)
    return jsonify(get_recent_logs(limit))

@app.route('/api/alerts')
@login_required
def api_alerts(): return jsonify(latest_alerts[-10:])

@app.route('/api/monitor/start', methods=['POST'])
@login_required
def start_monitor():
    global monitoring_active, monitor_thread
    if not monitoring_active:
        monitoring_active = True
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return jsonify({'status':'started','message':'Monitoring shuru!'})
    return jsonify({'status':'already_running'})

@app.route('/api/monitor/stop', methods=['POST'])
@login_required
def stop_monitor():
    global monitoring_active
    monitoring_active = False
    return jsonify({'status':'stopped'})

@app.route('/api/monitor/status')
@login_required
def monitor_status(): return jsonify({'active': monitoring_active})

@app.route('/api/simulate', methods=['POST'])
@login_required
def simulate_one():
    pkt    = simulate_packet()
    result = predict(pkt)
    insert_log(result)

    ip = result.get('src_ip','')
    if ip not in geo_cache:
        geo_cache[ip] = get_geoip(ip)
    result['geo'] = geo_cache[ip]

    if result['risk_level'] in ('HIGH','MEDIUM') and result['attack_type'] != 'normal':
        latest_alerts.append(result)
    return jsonify(result)

@app.route('/api/geomap')
@login_required
def api_geomap():
    logs = get_recent_logs(100)
    points = []
    for log in logs:
        ip = log.get('src_ip','')
        if ip not in geo_cache:
            geo_cache[ip] = get_geoip(ip)
        geo = geo_cache[ip]
        points.append({
            'lat':         geo['lat'],
            'lon':         geo['lon'],
            'country':     geo['country'],
            'city':        geo['city'],
            'flag':        geo['flag'],
            'attack_type': log.get('attack_type',''),
            'risk_level':  log.get('risk_level',''),
            'risk_score':  log.get('risk_score',0),
            'src_ip':      ip,
            'timestamp':   log.get('timestamp',''),
        })
    return jsonify(points)

@app.route('/api/report/generate', methods=['POST'])
@login_required
def generate_pdf():
    period   = request.json.get('period','Daily')
    filepath = generate_report(get_all_logs(), get_stats(), period)
    return jsonify({'file': filepath})

@app.route('/api/report/download')
@login_required
def download_report():
    filepath = request.args.get('file','')
    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True,
                         download_name=f"CyberShield_{datetime.now().strftime('%Y%m%d')}.pdf")
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/test/email', methods=['POST'])
@login_required
def test_email():
    try:
        send_email_alert(app, mail, {
            'attack_type':'test','src_ip':'127.0.0.1',
            'risk_score':99,'risk_level':'HIGH',
            'hindi_label':'Yeh ek test alert hai',
            'top_reason':'Manual test triggered',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'port':80
        })
        return jsonify({'status':'sent'})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)})

@app.route('/api/test/telegram', methods=['POST'])
@login_required
def test_telegram():
    try:
        send_telegram_alert(app.config['TELEGRAM_BOT_TOKEN'],
                            app.config['TELEGRAM_CHAT_ID'], {
            'attack_type':'test','src_ip':'127.0.0.1',
            'risk_score':99,'risk_level':'HIGH',
            'hindi_label':'Yeh ek test alert hai',
            'top_reason':'Manual test triggered',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'port':80
        })
        return jsonify({'status':'sent'})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)})

# ── Run ───────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    load_model()
    print("🛡️ CyberShield on http://127.0.0.1:5000")
    app.run(debug=True, threaded=True)