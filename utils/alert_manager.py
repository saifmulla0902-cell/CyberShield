# utils/alert_manager.py

import requests
from datetime import datetime

# ── Email Alert ──────────────────────────────────────────
def send_email_alert(app, mail, attack_data: dict):
    try:
        from flask_mail import Message
        subject = f"🚨 CyberShield Alert — {attack_data.get('attack_type','').upper()} Detected!"
        body = f"""
CyberShield Security Alert
===========================
Time       : {attack_data.get('timestamp', datetime.now())}
Attack Type: {attack_data.get('attack_type','').replace('_',' ').upper()}
Source IP  : {attack_data.get('src_ip','Unknown')}
Risk Score : {attack_data.get('risk_score', 0)}/100
Risk Level : {attack_data.get('risk_level','HIGH')}
Hindi Alert: {attack_data.get('hindi_label','')}

Top Reason : {attack_data.get('top_reason','')}

-- CyberShield | Rajarambapu Institute of Technology
        """
        with app.app_context():
            msg = Message(
                subject=subject,
                sender=app.config['MAIL_USERNAME'],
                recipients=[app.config['MAIL_RECEIVER']],
                body=body
            )
            mail.send(msg)
            print(f"✅ Email sent for {attack_data.get('attack_type')}")
    except Exception as e:
        print(f"❌ Email error: {e}")


# ── Telegram Alert ───────────────────────────────────────
def send_telegram_alert(bot_token: str, chat_id: str, attack_data: dict):
    try:
        risk = attack_data.get('risk_level','HIGH')
        icon = '🔴' if risk=='HIGH' else '🟡' if risk=='MEDIUM' else '🟢'
        text = f"""
{icon} *CyberShield Alert*

*Attack:* {attack_data.get('attack_type','').replace('_',' ').upper()}
*Source:* `{attack_data.get('src_ip','Unknown')}`
*Port:* {attack_data.get('port','')}
*Risk Score:* {attack_data.get('risk_score',0)}/100
*Level:* {risk}

_{attack_data.get('hindi_label','')}_

*Reason:* {attack_data.get('top_reason','')}
⏰ {attack_data.get('timestamp','')}
        """
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }, timeout=5)
        print(f"✅ Telegram sent for {attack_data.get('attack_type')}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


# ── GeoIP Lookup ─────────────────────────────────────────
def get_geoip(ip: str) -> dict:
    try:
        # Skip private IPs
        if ip.startswith(('192.168.','10.','172.','127.')):
            return {'lat':20.5937,'lon':78.9629,'country':'India (Local)',
                    'city':'Local Network','flag':'🇮🇳'}
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,lat,lon,countryCode",
                           timeout=3)
        d = res.json()
        if d.get('status') == 'success':
            return {
                'lat':     d.get('lat', 0),
                'lon':     d.get('lon', 0),
                'country': d.get('country', 'Unknown'),
                'city':    d.get('city', 'Unknown'),
                'flag':    country_flag(d.get('countryCode',''))
            }
    except:
        pass
    return {'lat': 20.5937, 'lon': 78.9629,
            'country': 'Unknown', 'city': 'Unknown', 'flag': '🌐'}


def country_flag(code: str) -> str:
    if not code or len(code) != 2:
        return '🌐'
    return chr(ord(code[0])+127397) + chr(ord(code[1])+127397)