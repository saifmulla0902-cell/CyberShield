import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os

LABELS = ['normal','ddos','brute_force','port_scan',
          'sql_injection','phishing','malware']

FEATURE_COLS = ['duration','src_bytes','dst_bytes','packet_count',
                'protocol_tcp','protocol_udp','protocol_icmp','port',
                'connection_rate','failed_logins','same_srv_rate','diff_srv_rate']

def generate_dataset(n=3000):
    np.random.seed(42)
    rows = []
    types  = LABELS
    weights = [0.4,0.15,0.1,0.1,0.1,0.1,0.05]
    for _ in range(n):
        t  = np.random.choice(types, p=weights)
        li = types.index(t)
        if t == 'normal':
            r = [np.random.randint(1,100), np.random.randint(100,5000),
                 np.random.randint(100,5000), np.random.randint(1,50),
                 1,0,0, np.random.choice([80,443,8080]),
                 np.random.uniform(0.1,2), 0,
                 np.random.uniform(0.7,1), np.random.uniform(0,0.1)]
        elif t == 'ddos':
            r = [np.random.randint(0,3), np.random.randint(40,100),
                 np.random.randint(0,50), np.random.randint(500,10000),
                 0,1,0, np.random.randint(1,65535),
                 np.random.uniform(100,500), 0,
                 np.random.uniform(0.9,1), np.random.uniform(0,0.05)]
        elif t == 'brute_force':
            r = [np.random.randint(1,10), np.random.randint(200,500),
                 np.random.randint(100,300), np.random.randint(50,200),
                 1,0,0, np.random.choice([22,3389,21]),
                 np.random.uniform(5,30), np.random.randint(10,100),
                 np.random.uniform(0.9,1), np.random.uniform(0,0.05)]
        elif t == 'port_scan':
            r = [np.random.randint(0,2), np.random.randint(40,80),
                 np.random.randint(0,40), np.random.randint(100,1000),
                 1,0,0, np.random.randint(1,65535),
                 np.random.uniform(10,100), 0,
                 np.random.uniform(0,0.2), np.random.uniform(0.8,1)]
        elif t == 'sql_injection':
            r = [np.random.randint(1,30), np.random.randint(500,3000),
                 np.random.randint(1000,10000), np.random.randint(10,100),
                 1,0,0, np.random.choice([80,443,3306]),
                 np.random.uniform(0.5,5), np.random.randint(0,5),
                 np.random.uniform(0.5,0.9), np.random.uniform(0.1,0.5)]
        elif t == 'phishing':
            r = [np.random.randint(5,60), np.random.randint(1000,8000),
                 np.random.randint(5000,20000), np.random.randint(20,150),
                 1,0,0, np.random.choice([80,443]),
                 np.random.uniform(0.1,1), 0,
                 np.random.uniform(0.3,0.7), np.random.uniform(0.3,0.7)]
        else:  # malware
            r = [np.random.randint(100,3600), np.random.randint(5000,50000),
                 np.random.randint(1000,10000), np.random.randint(200,2000),
                 1,0,0, np.random.choice([4444,1337,6666]),
                 np.random.uniform(1,20), np.random.randint(0,3),
                 np.random.uniform(0.8,1), np.random.uniform(0,0.2)]
        rows.append(r + [li])
    cols = FEATURE_COLS + ['label']
    return pd.DataFrame(rows, columns=cols)


def train_model():
    print("Generating dataset...")
    df = generate_dataset(3000)

    X = df[FEATURE_COLS].values.astype(float)
    y = df['label'].values.astype(int)

    # Manual normalize — no sklearn
    mean = X.mean(axis=0)
    std  = X.std(axis=0) + 1e-8
    X_sc = (X - mean) / std

    # Manual split
    np.random.seed(42)
    idx   = np.random.permutation(len(X_sc))
    split = int(len(X_sc) * 0.8)
    X_train, X_test = X_sc[idx[:split]], X_sc[idx[split:]]
    y_train, y_test = y[idx[:split]],    y[idx[split:]]

    print("Training XGBoost...")
    model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        eval_metric='mlogloss',
        random_state=42
    )
    model.fit(X_train, y_train)

    acc = (model.predict(X_test) == y_test).mean()
    print(f"Accuracy: {acc*100:.2f}%")

    os.makedirs('model', exist_ok=True)
    joblib.dump(model,        'model/xgb_model.pkl')
    joblib.dump(mean,         'model/mean.pkl')
    joblib.dump(std,          'model/std.pkl')
    joblib.dump(LABELS,       'model/labels.pkl')
    joblib.dump(FEATURE_COLS, 'model/feature_cols.pkl')
    print("Model saved!")


if __name__ == '__main__':
    train_model()