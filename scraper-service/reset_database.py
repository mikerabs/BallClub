import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# SQL script to drop and recreate tables
RESET_DATABASE_SQL = """
-- Drop existing tables if they exist
DROP TABLE IF EXISTS jersey_numbers CASCADE;
DROP TABLE IF EXISTS player_colleges CASCADE;
DROP TABLE IF EXISTS player_teams CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS players CASCADE;

-- Create Players Table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    sport TEXT NOT NULL DEFAULT 'Baseball',
    url TEXT UNIQUE NOT NULL
);

-- Create Teams Table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Create Player-Teams Table
CREATE TABLE player_teams (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    team_id INT REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE (player_id, team_id)
);

-- Create Player-Colleges Table (Supports multiple colleges per player)
CREATE TABLE player_colleges (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    college TEXT NOT NULL,
    UNIQUE (player_id, college)
);

-- Create Jersey Numbers Table (Supports multiple numbers per player per team)
CREATE TABLE jersey_numbers (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id) ON DELETE CASCADE,
    team_id INT REFERENCES teams(id) ON DELETE CASCADE,
    number INT NOT NULL,
    UNIQUE (player_id, team_id, number)
);
"""

# Function to reset the database
def reset_database():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(RESET_DATABASE_SQL)
        conn.commit()
        print("Database reset and recreated successfully.")
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    reset_database()

