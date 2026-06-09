import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
import xgboost as xgb
import joblib
import os

def generate_dataset(n=5000):
    np.random.seed(42)
    data = []
    types = ['normal','ddos','brute_force','port_scan','sql_injection','phishing','malware']
    weights = [0.4,0.15,0.1,0.1,0.1,0.1,0.05]

    for _ in range(n):
        t = np.random.choice(types, p=weights)
        if t == 'normal':
            r = dict(duration=np.random.randint(1,100), src_bytes=np.random.randint(100,5000),
                     dst_bytes=np.random.randint(100,5000), packet_count=np.random.randint(1,50),
                     protocol_tcp=1, protocol_udp=0, protocol_icmp=0,
                     port=np.random.choice([80,443,8080]),
                     connection_rate=np.random.uniform(0.1,2),
                     failed_logins=0, same_srv_rate=np.random.uniform(0.7,1),
                     diff_srv_rate=np.random.uniform(0,0.1), label='normal')
        elif t == 'ddos':
            r = dict(duration=np.random.randint(0,3), src_bytes=np.random.randint(40,100),
                     dst_bytes=np.random.randint(0,50), packet_count=np.random.randint(500,10000),
                     protocol_tcp=0, protocol_udp=1, protocol_icmp=0,
                     port=np.random.randint(1,65535),
                     connection_rate=np.random.uniform(100,500),
                     failed_logins=0, same_srv_rate=np.random.uniform(0.9,1),
                     diff_srv_rate=np.random.uniform(0,0.05), label='ddos')
        elif t == 'brute_force':
            r = dict(duration=np.random.randint(1,10), src_bytes=np.random.randint(200,500),
                     dst_bytes=np.random.randint(100,300), packet_count=np.random.randint(50,200),
                     protocol_tcp=1, protocol_udp=0, protocol_icmp=0,
                     port=np.random.choice([22,3389,21]),
                     connection_rate=np.random.uniform(5,30),
                     failed_logins=np.random.randint(10,100),
                     same_srv_rate=np.random.uniform(0.9,1),
                     diff_srv_rate=np.random.uniform(0,0.05), label='brute_force')
        elif t == 'port_scan':
            r = dict(duration=np.random.randint(0,2), src_bytes=np.random.randint(40,80),
                     dst_bytes=np.random.randint(0,40), packet_count=np.random.randint(100,1000),
                     protocol_tcp=1, protocol_udp=0, protocol_icmp=0,
                     port=np.random.randint(1,65535),
                     connection_rate=np.random.uniform(10,100),
                     failed_logins=0, same_srv_rate=np.random.uniform(0,0.2),
                     diff_srv_rate=np.random.uniform(0.8,1), label='port_scan')
        elif t == 'sql_injection':
            r = dict(duration=np.random.randint(1,30), src_bytes=np.random.randint(500,3000),
                     dst_bytes=np.random.randint(1000,10000), packet_count=np.random.randint(10,100),
                     protocol_tcp=1, protocol_udp=0, protocol_icmp=0,
                     port=np.random.choice([80,443,3306]),
                     connection_rate=np.random.uniform(0.5,5),
                     failed_logins=np.random.randint(0,5),
                     same_srv_rate=np.random.uniform(0.5,0.9),
                     diff_srv_rate=np.random.uniform(0.1,0.5), label='sql_injection')
        elif t == 'phishing':
            r = dict(duration=np.random.randint(5,60), src_bytes=np.random.randint(1000,8000),
                     dst_bytes=np.random.randint(5000,20000), packet_count=np.random.randint(20,150),
                     protocol_tcp=1, protocol_udp=0, protocol_icmp=0,
                     port=np.random.choice([80,443]),
                     connection_rate=np.random.uniform(0.1,1),
                     failed_logins=0, same_srv_rate=np.random.uniform(0.3,0.7),
                     diff_srv_rate=np.random.uniform(0.3,0.7), label='phishing')
        else:
            r = dict(duration=np.random.randint(100,3600), src_bytes=np.random.randint(5000,50000),
                     dst_bytes=np.random.randint(1000,10000), packet_count=np.random.randint(200,2000),
                     protocol_tcp=1, protocol_udp=0, protocol_icmp=0,
                     port=np.random.choice([4444,1337,6666,8888]),
                     connection_rate=np.random.uniform(1,20),
                     failed_logins=np.random.randint(0,3),
                     same_srv_rate=np.random.uniform(0.8,1),
                     diff_srv_rate=np.random.uniform(0,0.2), label='malware')
        data.append(r)
    return pd.DataFrame(data)

def train_model():
    print("Generating dataset...")
    df = generate_dataset(5000)
    feature_cols = ['duration','src_bytes','dst_bytes','packet_count',
                    'protocol_tcp','protocol_udp','protocol_icmp','port',
                    'connection_rate','failed_logins','same_srv_rate','diff_srv_rate']
    X = df[feature_cols]
    y = df['label']
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_sc, y_enc, test_size=0.2, random_state=42)
    model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                               eval_metric='mlogloss', random_state=42)
    model.fit(X_train, y_train)
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"Accuracy: {acc*100:.2f}%")
    os.makedirs('model', exist_ok=True)
    joblib.dump(model,  'model/xgb_model.pkl')
    joblib.dump(scaler, 'model/scaler.pkl')
    joblib.dump(le,     'model/label_encoder.pkl')
    joblib.dump(feature_cols, 'model/feature_cols.pkl')
    print("Model saved!")

if __name__ == '__main__':
    train_model()