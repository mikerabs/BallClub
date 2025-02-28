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

BASE_URL = "https://www.baseball-reference.com/players/{}/"

# Function to check if a player exists in the database
def player_exists(player_name):
    cur.execute("SELECT 1 FROM players WHERE name = %s", (player_name,))
    return cur.fetchone() is not None

# Function to scrape player names
def scrape_players():
    letters = "a"
    for letter in letters:
        url = BASE_URL.format(letter)
        print(f"Scraping: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch {url} (Status Code: {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract player names from <p> tags
            for p in soup.find_all("p"):
                a_tag = p.find("a")
                if not a_tag:
                    continue

                player_name = a_tag.text.strip()
                player_url = "https://www.baseball-reference.com" + a_tag["href"]

                # Remove Hall of Fame (+) markers from names
                player_name = player_name.replace("+", "").strip()

                # Skip player if already in database
                if player_exists(player_name):
                    print(f"Skipping existing player: {player_name}")
                    continue

                # Insert into database
                cur.execute(
                    "INSERT INTO players (name, sport) VALUES (%s, 'Baseball');",
                    (player_name,)
                )
                conn.commit()
                print(f"Added: {player_name}")

            # Random delay to avoid being blocked
            delay = random.uniform(1.5, 4.0)
            print(f"Sleeping for {delay:.2f} seconds...")
            time.sleep(delay)

        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {e}")

    cur.close()
    conn.close()
    print("Scraping completed.")

# Run the scraper
if __name__ == "__main__":
    scrape_players()

