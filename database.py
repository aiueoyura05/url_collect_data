import json
import sqlite3
import time
from datetime import datetime,timezone
import logging
import requests

# phishtank_url = 'http://data.phishtank.com/data/online-valid.json'
DB_PATH = 'phishtank0727.db'
JSON_URL = 'TEST_URL'
FETCH_INTERVAL = 3600 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def fetch_json_data(url):
    """URLからJSONデータを取得"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching JSON data: {e}")
        return None

def initialize_database(db_path):
    """データベースの初期化"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS phish_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phish_id INTEGER UNIQUE,
        url TEXT,
        submission_time DATETIME,
        verified TEXT,
        verification_time DATETIME,
        online TEXT,
        timestamp DATETIME
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS phish_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phish_id INTEGER,
        ip_address TEXT,
        cidr_block TEXT,
        announcing_network TEXT,
        rir TEXT,
        country TEXT,
        detail_time DATETIME,
        FOREIGN KEY (phish_id) REFERENCES phish_data (phish_id)
    )
    ''')
    conn.commit()
    conn.close()

def update_database(data, db_path):
    """データベースを更新"""
    if data is None:
        logger.warning("No data to update")
        return

    current_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for entry in data:
        phish_id = entry['phish_id']

        # データベース内に存在するか確認
        c.execute('SELECT 1 FROM phish_data WHERE phish_id = ?', (phish_id,))
        exists = c.fetchone()

        if not exists:
            url = entry['url']
            submission_time = entry['submission_time']
            verified = entry['verified']
            verification_time = entry['verification_time']
            online = entry['online']
            timestamp = current_time_utc

            c.execute('''
            INSERT INTO phish_data (phish_id, url, submission_time, verified, verification_time, online, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (phish_id, url, submission_time, verified, verification_time, online, timestamp))

            for detail in entry['details']:
                ip_address = detail['ip_address']
                cidr_block = detail['cidr_block']
                announcing_network = detail['announcing_network']
                rir = detail['rir']
                country = detail['country']
                detail_time = detail['detail_time']

                c.execute('''
                INSERT INTO phish_details (phish_id, ip_address, cidr_block, announcing_network, rir, country, detail_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (phish_id, ip_address, cidr_block, announcing_network, rir, country, detail_time))

    conn.commit()
    conn.close()
    logger.info("Database updated successfully")



def main():
    initialize_database(DB_PATH)
    while True:
        start_time = time.time()
        data = fetch_json_data(JSON_URL)
        update_database(data, DB_PATH)
        elapsed_time = time.time() - start_time
        logger.info(f"Fetch and update completed in {elapsed_time:.2f} seconds")
        time.sleep(FETCH_INTERVAL)

if __name__ == '__main__':
    main()