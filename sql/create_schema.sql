-- Tabla de usuarios
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    city TEXT
);

-- Preferencias de usuario (separa múltiples intereses)
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    preference TEXT NOT NULL
);

-- Lugares donde se realizan eventos
CREATE TABLE venues (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    address TEXT,
    capacity INT
);

-- Eventos
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    tags TEXT[],
    venue_id INT REFERENCES venues(id) ON DELETE SET NULL
);

-- Interacciones (likes, dislikes, registros, etc.)
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    type TEXT CHECK (type IN ('like','dislike','view','register')),
    ts TIMESTAMP DEFAULT NOW()
);