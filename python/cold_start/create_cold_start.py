import random
import json
from faker import Faker
from datetime import timedelta
import psycopg2

# =========================
# Cargar configuración desde /conf/db.json
# =========================
def load_db_config():
    with open("../../conf/db.json", "r") as f:
        return json.load(f)

config = load_db_config()

DB_USER = config["DB_USER"]
DB_PASS = config["DB_PASS"]
DB_NAME = config["DB_NAME"]
DB_HOST = config["DB_HOST"]
DB_PORT = config["DB_PORT"]

# =========================
# Parámetros y Faker
# =========================
fake = Faker("es_ES")

NUM_USERS = 10
NUM_VENUES = 5
NUM_EVENTS = 15
NUM_INTERACTIONS = 30

preferences_pool = ["music", "art", "tech", "sports", "food", "business", "culture", "rock", "dance"]

# =========================
# Inserción de datos
# =========================
def insert_data():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    # Users
    for i in range(1, NUM_USERS + 1):
        cur.execute(
            "INSERT INTO users (id, name, email, city) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;",
            (i, fake.name(), fake.unique.email(), fake.city())
        )

    # User preferences
    for user_id in range(1, NUM_USERS + 1):
        for _ in range(random.randint(1, 3)):
            pref = random.choice(preferences_pool)
            cur.execute(
                "INSERT INTO user_preferences (user_id, preference) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (user_id, pref)
            )

    # Venues
    for i in range(1, NUM_VENUES + 1):
        cur.execute(
            "INSERT INTO venues (id, name, city, address, capacity) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;",
            (
                i,
                fake.company(),
                fake.city(),
                fake.address().replace("\n", " "),
                random.randint(100, 20000),
            )
        )

    # Events
    for i in range(1, NUM_EVENTS + 1):
        start_time = fake.date_time_between(start_date="+1d", end_date="+30d")
        end_time = start_time + timedelta(hours=random.randint(2, 5))
        tags = random.sample(preferences_pool, random.randint(1, 3))
        venue_id = random.randint(1, NUM_VENUES)
        cur.execute(
            "INSERT INTO events (id, name, description, start_time, end_time, tags, venue_id) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;",
            (
                i,
                fake.catch_phrase(),
                fake.text(50),
                start_time,
                end_time,
                tags,   # ARRAY en Postgres
                venue_id, 
            )
        )

    # Interactions
    types = ["like", "dislike", "register"]
    for _ in range(NUM_INTERACTIONS):
        user_id = random.randint(1, NUM_USERS)
        event_id = random.randint(1, NUM_EVENTS)
        type_ = random.choice(types)
        ts = fake.date_time_between(start_date="-30d", end_date="now")
        cur.execute(
            "INSERT INTO interactions (user_id, event_id, type, ts) VALUES (%s, %s, %s, %s);",
            (user_id, event_id, type_, ts)
        )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Datos de prueba insertados en Cloud SQL con éxito.")

# =========================
# Main
# =========================
if __name__ == "__main__":
    insert_data()
