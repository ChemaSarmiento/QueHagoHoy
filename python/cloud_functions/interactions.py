import json
import psycopg2
import os
from google.cloud import pubsub_v1, storage
import functions_framework

BUCKET_NAME = os.getenv("CONFIG_BUCKET", "my-config-bucket")
CONFIG_FILE = os.getenv("CONFIG_FILE", "conf/db.json")
PROJECT_ID = os.getenv("GCP_PROJECT", "my-project")
TOPIC_ID = os.getenv("PUBSUB_TOPIC", "user-interactions")

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
def interactions(request):
    if request.method != "POST":
        return ("Método no soportado", 405)

    data = request.get_json()
    user_id = data.get("user_id")
    event_id = data.get("event_id")
    type_ = data.get("type")  # like, dislike, register
    ts = data.get("ts")

    if not all([user_id, event_id, type_]):
        return ("Faltan parámetros", 400)

    # Guardar en BD
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO interactions (user_id, event_id, type, ts) VALUES (%s, %s, %s, %s);",
        (user_id, event_id, type_, ts)
    )
    conn.commit()
    cur.close()
    conn.close()

    # Publicar en Pub/Sub
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    message_json = json.dumps(data).encode("utf-8")
    publisher.publish(topic_path, message_json)

    return (json.dumps({"status": "ok"}), 200, {"Content-Type": "application/json"})
