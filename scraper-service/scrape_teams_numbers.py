import os
import time
import random
import requests
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Function to check if a team exists
def team_exists(team_name):
    cur.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
    return cur.fetchone()

# Function to insert a new team and return its ID
def insert_team(team_name):
    cur.execute("INSERT INTO teams (name) VALUES (%s) RETURNING id", (team_name,))
    team_id = cur.fetchone()[0]
    conn.commit()
    return team_id

# Function to check if a player-team relationship exists
def player_team_exists(player_id, team_id):
    cur.execute("SELECT 1 FROM player_teams WHERE player_id = %s AND team_id = %s", (player_id, team_id))
    return cur.fetchone() is not None

# Function to insert a new player-team relationship
def insert_player_team(player_id, team_id):
    cur.execute("INSERT INTO player_teams (player_id, team_id) VALUES (%s, %s)", (player_id, team_id))
    conn.commit()

# Function to check if a jersey number exists for a player on a team
def jersey_number_exists(player_id, team_id, number):
    cur.execute("SELECT 1 FROM jersey_numbers WHERE player_id = %s AND team_id = %s AND number = %s",
                (player_id, team_id, number))
    return cur.fetchone() is not None

# Function to insert a new jersey number for a player on a team
def insert_jersey_number(player_id, team_id, number):
    cur.execute("INSERT INTO jersey_numbers (player_id, team_id, number) VALUES (%s, %s, %s)",
                (player_id, team_id, number))
    conn.commit()

# Function to scrape teams and jersey numbers for all players in the database
def scrape_teams_and_numbers():
    cur.execute("SELECT id, url FROM players")
    players = cur.fetchall()

    for player_id, player_url in players:
        print(f"Scraping teams & jersey numbers for player: {player_url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(player_url, headers=headers)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                print(f"Failed to fetch {player_url} (Status Code: {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Locate the section with team & jersey number info
            uni_holder = soup.find("div", class_="uni_holder br")
            if not uni_holder:
                print(f"No team/jersey info found for {player_url}")
                continue

            for a_tag in uni_holder.find_all("a", class_="poptip"):
                # Extract jersey number from the href attribute
                href = a_tag.get("href", "")
                if "number=" in href:
                    number = href.split("number=")[-1]
                else:
                    continue  # Skip if no number found

                # Extract team name from the data-tip attribute
                data_tip = a_tag.get("data-tip", "")
                if "-" not in data_tip:
                    continue  # Skip if no valid team-year format

                team_name = data_tip.split(" ", 1)[1]  # Get everything after the year(s)
                team_name = team_name.strip()

                # Ensure team exists in the database
                team_id = team_exists(team_name)
                if not team_id:
                    team_id = insert_team(team_name)
                    print(f"Added new team: {team_name}")
                else:
                    team_id = team_id[0]

                # Ensure player-team relationship exists
                if not player_team_exists(player_id, team_id):
                    insert_player_team(player_id, team_id)
                    print(f"Linked {player_url} to team {team_name}")

                # Ensure jersey number is added
                if not jersey_number_exists(player_id, team_id, number):
                    insert_jersey_number(player_id, team_id, number)
                    print(f"Added jersey number {number} for {player_url} ({team_name})")

            # Random delay to avoid being blocked
            delay = random.uniform(1.5, 4.0)
            print(f"Sleeping for {delay:.2f} seconds...")
            time.sleep(delay)

        except requests.exceptions.RequestException as e:
            print(f"Request error for {player_url}: {e}")

    cur.close()
    conn.close()
    print("Team & jersey number scraping completed.")

# Run the scraper
if __name__ == "__main__":
    scrape_teams_and_numbers()

