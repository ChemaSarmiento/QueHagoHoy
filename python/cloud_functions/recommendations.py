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
def recommendations(request):
    user_id = request.args.get("user_id")
    limit = int(request.args.get("limit", 5))

    if not user_id:
        return ("user_id requerido", 400)

    conn = get_connection()
    cur = conn.cursor()

    # Perfil del usuario
    cur.execute("SELECT city FROM users WHERE id=%s;", (user_id,))
    user_row = cur.fetchone()
    if not user_row:
        return ("Usuario no encontrado", 404)
    user_city = user_row[0]

    cur.execute("SELECT preference FROM user_preferences WHERE user_id=%s;", (user_id,))
    prefs = [r[0] for r in cur.fetchall()]

    # Buscar eventos que hagan match
    cur.execute("""
        SELECT e.id, e.name, e.description, e.start_time, e.end_time, e.tags, e.venue_id
        FROM events e
        JOIN venues v ON e.venue_id = v.id
        WHERE v.city=%s OR EXISTS (
            SELECT 1 FROM unnest(e.tags) t WHERE t = ANY(%s)
        )
        LIMIT %s;
    """, (user_city, prefs, limit))
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

    return (json.dumps({"events": events}), 200, {"Content-Type": "application/json"})
