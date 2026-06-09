import joblib
import numpy as np
import random
import os
from datetime import datetime

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'model')

_model  = None
_mean   = None
_std    = None
_labels = None
_fcols  = None

HINDI = {
    'ddos':          'DDoS Hamla — Network Flood Ho Raha Hai!',
    'brute_force':   'Brute Force — Password Crack Karne Ki Koshish!',
    'port_scan':     'Port Scan — Hacker Network Dekh Raha Hai!',
    'sql_injection': 'SQL Injection — Database Attack!',
    'phishing':      'Phishing — Fake Link Bheja Ja Raha Hai!',
    'malware':       'Malware — Virus Detect Hua!',
    'normal':        'Sab Theek Hai — Normal Traffic'
}

REASONS = {
    'ddos':          ['Packet count bahut zyada tha — flood pattern',
                      'Packet size abnormally chhota',
                      'UDP pe continuous traffic'],
    'brute_force':   ['Multiple failed login attempts detected',
                      'SSH/RDP port pe repeated connections',
                      'High connection rate same server'],
    'port_scan':     ['Multiple ports pe sequential connections',
                      'Very short connection duration',
                      'High diff_srv_rate detected'],
    'sql_injection': ['Database port pe unusual payload',
                      'Abnormal HTTP POST data size',
                      'Port 3306 pe suspicious activity'],
    'phishing':      ['Suspicious domain se large data transfer',
                      'Unusual HTTP redirect pattern',
                      'Mixed srv rate — fake site pattern'],
    'malware':       ['Port 4444 pe long duration connection',
                      'Suspicious outbound data transfer',
                      'Known C2 server port detected'],
    'normal':        ['Connection pattern normal hai',
                      'Standard protocol use ho raha hai',
                      'Traffic volume acceptable range mein']
}


def load_model():
    global _model, _mean, _std, _labels, _fcols
    try:
        _model  = joblib.load(os.path.join(MODEL_DIR, 'xgb_model.pkl'))
        _mean   = joblib.load(os.path.join(MODEL_DIR, 'mean.pkl'))
        _std    = joblib.load(os.path.join(MODEL_DIR, 'std.pkl'))
        _labels = joblib.load(os.path.join(MODEL_DIR, 'labels.pkl'))
        _fcols  = joblib.load(os.path.join(MODEL_DIR, 'feature_cols.pkl'))
        print("✅ Model loaded!")
        return True
    except Exception as e:
        print(f"⚠️ Model not found: {e}")
        return False


def get_risk_score(conf, atype):
    if atype == 'normal':
        return int(conf * 33)
    elif atype in ['port_scan', 'phishing']:
        return int(34 + conf * 32)
    else:
        return int(67 + conf * 33)


def simulate_packet():
    types   = ['normal','ddos','brute_force','port_scan',
               'sql_injection','phishing','malware']
    weights = [0.5, 0.1, 0.1, 0.1, 0.08, 0.07, 0.05]
    t = random.choices(types, weights=weights)[0]

    src_ip = (f"{random.randint(1,254)}."
              f"{random.randint(0,254)}."
              f"{random.randint(0,254)}."
              f"{random.randint(1,254)}")

    base = {'src_ip': src_ip, 'dst_ip': f"192.168.1.{random.randint(1,10)}"}

    if t == 'normal':
        base.update(dict(duration=random.randint(1,100),
            src_bytes=random.randint(100,5000),
            dst_bytes=random.randint(100,5000),
            packet_count=random.randint(1,50),
            protocol_tcp=1,protocol_udp=0,protocol_icmp=0,
            port=random.choice([80,443,8080]),
            connection_rate=round(random.uniform(0.1,2),2),
            failed_logins=0,
            same_srv_rate=round(random.uniform(0.7,1),2),
            diff_srv_rate=round(random.uniform(0,0.1),2),
            protocol='TCP'))
    elif t == 'ddos':
        base.update(dict(duration=random.randint(0,3),
            src_bytes=random.randint(40,100),
            dst_bytes=random.randint(0,50),
            packet_count=random.randint(500,10000),
            protocol_tcp=0,protocol_udp=1,protocol_icmp=0,
            port=random.randint(1,65535),
            connection_rate=round(random.uniform(100,500),2),
            failed_logins=0,
            same_srv_rate=round(random.uniform(0.9,1),2),
            diff_srv_rate=round(random.uniform(0,0.05),2),
            protocol='UDP'))
    elif t == 'brute_force':
        base.update(dict(duration=random.randint(1,10),
            src_bytes=random.randint(200,500),
            dst_bytes=random.randint(100,300),
            packet_count=random.randint(50,200),
            protocol_tcp=1,protocol_udp=0,protocol_icmp=0,
            port=random.choice([22,3389,21]),
            connection_rate=round(random.uniform(5,30),2),
            failed_logins=random.randint(10,100),
            same_srv_rate=round(random.uniform(0.9,1),2),
            diff_srv_rate=round(random.uniform(0,0.05),2),
            protocol='TCP'))
    elif t == 'port_scan':
        base.update(dict(duration=random.randint(0,2),
            src_bytes=random.randint(40,80),
            dst_bytes=random.randint(0,40),
            packet_count=random.randint(100,1000),
            protocol_tcp=1,protocol_udp=0,protocol_icmp=0,
            port=random.randint(1,65535),
            connection_rate=round(random.uniform(10,100),2),
            failed_logins=0,
            same_srv_rate=round(random.uniform(0,0.2),2),
            diff_srv_rate=round(random.uniform(0.8,1),2),
            protocol='TCP'))
    elif t == 'sql_injection':
        base.update(dict(duration=random.randint(1,30),
            src_bytes=random.randint(500,3000),
            dst_bytes=random.randint(1000,10000),
            packet_count=random.randint(10,100),
            protocol_tcp=1,protocol_udp=0,protocol_icmp=0,
            port=random.choice([80,443,3306]),
            connection_rate=round(random.uniform(0.5,5),2),
            failed_logins=random.randint(0,5),
            same_srv_rate=round(random.uniform(0.5,0.9),2),
            diff_srv_rate=round(random.uniform(0.1,0.5),2),
            protocol='TCP'))
    elif t == 'phishing':
        base.update(dict(duration=random.randint(5,60),
            src_bytes=random.randint(1000,8000),
            dst_bytes=random.randint(5000,20000),
            packet_count=random.randint(20,150),
            protocol_tcp=1,protocol_udp=0,protocol_icmp=0,
            port=random.choice([80,443]),
            connection_rate=round(random.uniform(0.1,1),2),
            failed_logins=0,
            same_srv_rate=round(random.uniform(0.3,0.7),2),
            diff_srv_rate=round(random.uniform(0.3,0.7),2),
            protocol='TCP'))
    else:  # malware
        base.update(dict(duration=random.randint(100,3600),
            src_bytes=random.randint(5000,50000),
            dst_bytes=random.randint(1000,10000),
            packet_count=random.randint(200,2000),
            protocol_tcp=1,protocol_udp=0,protocol_icmp=0,
            port=random.choice([4444,1337,6666]),
            connection_rate=round(random.uniform(1,20),2),
            failed_logins=random.randint(0,3),
            same_srv_rate=round(random.uniform(0.8,1),2),
            diff_srv_rate=round(random.uniform(0,0.2),2),
            protocol='TCP'))
    return base


def predict(features):
    global _model, _mean, _std, _labels, _fcols

    # Load model if not loaded
    if _model is None:
        load_model()

    # Fallback demo mode agar model nahi mila
    if _model is None:
        atype = random.choice(['normal','ddos','brute_force','port_scan'])
        conf  = round(random.uniform(0.7, 0.99), 2)
        score = get_risk_score(conf, atype)
        level = 'HIGH' if score > 66 else 'MEDIUM' if score > 33 else 'LOW'
        return _build(atype, conf, score, level, features)

    # Predict
    fv   = np.array([[features.get(c, 0) for c in _fcols]], dtype=float)
    fv_sc = (fv - _mean) / (_std + 1e-8)

    idx   = int(_model.predict(fv_sc)[0])
    proba = _model.predict_proba(fv_sc)[0]
    conf  = float(proba[idx])
    atype = _labels[idx]

    score = get_risk_score(conf, atype)
    level = 'HIGH' if score > 66 else 'MEDIUM' if score > 33 else 'LOW'
    return _build(atype, conf, score, level, features)


def _build(atype, conf, score, level, features):
    return {
        'attack_type':  atype,
        'confidence':   round(conf, 2),
        'risk_score':   score,
        'risk_level':   level,
        'hindi_label':  HINDI.get(atype, ''),
        'top_reasons':  REASONS.get(atype, []),
        'top_reason':   REASONS.get(atype, [''])[0],
        'timestamp':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'src_ip':       features.get('src_ip', '0.0.0.0'),
        'dst_ip':       features.get('dst_ip', '192.168.1.1'),
        'protocol':     features.get('protocol', 'TCP'),
        'port':         features.get('port', 80),
        'packet_count': features.get('packet_count', 0),
        'src_bytes':    features.get('src_bytes', 0),
        'dst_bytes':    features.get('dst_bytes', 0),
    }