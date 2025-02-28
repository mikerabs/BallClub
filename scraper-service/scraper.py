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

# Function to check if a player URL already exists
def player_url_exists(player_url):
    cur.execute("SELECT 1 FROM players WHERE url = %s", (player_url,))
    return cur.fetchone() is not None

# Function to scrape player names
def scrape_players():
    letters = "a"#bcdefghijklmnopqrstuvwxyz"
    for letter in letters:
        url = BASE_URL.format(letter)
        print(f"Scraping: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'  # Ensure correct character encoding
            if response.status_code != 200:
                print(f"Failed to fetch {url} (Status Code: {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract player names from <p> tags
            for p in soup.find_all("p"):
                a_tag = p.find("a")
                if not a_tag or not a_tag.get("href"):
                    continue

                player_name = a_tag.text.strip()
                player_url = "https://www.baseball-reference.com" + a_tag["href"]

                # Remove Hall of Fame (+) markers from names
                player_name = player_name.replace("+", "").strip()

                # Validate that this is a player profile URL (not a random link)
                if not player_url.startswith("https://www.baseball-reference.com/players/"):
                    continue

                # Skip non-player links (like "Player Index")
                if not player_url.endswith(".shtml"):
                    print(f"Skipping non-player link: {player_name} ({player_url})")
                    continue
                
                if player_url_exists(player_url):
                    print(f"Skipping existing player profile: {player_url}")
                    continue

                # Insert into database
                cur.execute(
                    "INSERT INTO players (name, sport, url) VALUES (%s, 'Baseball', %s);",
                    (player_name, player_url)
                )
                conn.commit()
                print(f"Added: {player_name} ({player_url})")

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
