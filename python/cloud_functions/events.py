import json
import psycopg2
import os
from google.cloud import storage
import functions_framework

BUCKET_NAME = os.getenv("CONFIG_BUCKET", "my-config-bucket")
CONFIG_FILE = os.getenv("CONFIG_FILE", "conf/db.json")

_config_cache = None

def load_config():
    global _config_cache
    if _config_cache:
        return _config_cache
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(CONFIG_FILE)
    _config_cache = json.loads(blob.download_as_text())
    return _config_cache

def get_connection():
    config = load_config()
    return psycopg2.connect(
        dbname=config["DB_NAME"],
        user=config["DB_USER"],
        password=config["DB_PASS"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
    )

@functions_framework.http
def events(request):
    if request.method == "GET":
        return list_events()
    elif request.method == "POST":
        return create_event(request)
    else:
        return ("Método no soportado", 405)

def list_events():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, start_time, end_time, tags, venue_id FROM events;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    events = [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "start_time": str(r[3]),
            "end_time": str(r[4]),
            "tags": r[5],
            "venue_id": r[6]
        }
        for r in rows
    ]
    return (json.dumps(events), 200, {"Content-Type": "application/json"})

def create_event(request):
    data = request.get_json()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (name, description, start_time, end_time, tags, venue_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;",
        (data["name"], data["description"], data["start_time"], data["end_time"], data["tags"], data["venue_id"])
    )
    event_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return (json.dumps({"id": event_id}), 201, {"Content-Type": "application/json"})
