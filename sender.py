import random
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
from dotenv import load_dotenv
import json
from models import Song
import csv


def authenticate_spotify():
    """Authenticate and return a Spotify client instance."""
# Load environment variables from a .env file in the project root
    load_dotenv()

    CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    REDIRECT_URI = "http://127.0.0.1:8080/"

    # 'playlist-modify-public' is a permission scope allowing the script to give writable access to a user's public playlists.
    SCOPE = "playlist-modify-public playlist-modify-private"

    # Error message if the ID and secret were not loaded
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in environment."
        )

    # Create a credential manager
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE, cache_path=".spotifycache")

    # Setup the main spotify object
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


def get_current_user_id(sp: spotipy.Spotify):
    """Get the current authenticated user's Spotify ID."""
    user = sp.current_user()
    if user:
        return user["id"]
    else:
        raise RuntimeError("Failed to get current user from Spotify API.")


def load_song_cache(path=".cache") -> dict:
    """Load the song cache from the .cache file if it exists."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_song_cache(cache: dict, path=".cache"):
    """Save the song cache to the .cache file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)


def get_song_from_first_word(word: str, sp: spotipy.Spotify) -> Song | None:
    """Search for a track by the first word and return the raw API response."""
    word = word.strip('.,!?;"\'').split()[0]  # Get the first word only
    song = None

    cache = load_song_cache()

    # Check if the word is already in the cache
    if cache.get(word):
        print(f"Found '{word}' in cache. Using cached data...")
        song = random.choice(cache[word])
        return Song(song["track_id"], song["name"], song["spotify_url"])
    # If not in cache, search Spotify
    else:
        print(f"Searching Spotify for the word '{word}'...")
        results = sp.search(q=f'"{word}"', type='track', limit=10)

        if results:
            songs = [Song(
                track_id=song['id'], name=song['name'], spotify_url=song['external_urls']['spotify']
            ) for song in results['tracks']['items'] if song['name'].split()[0].strip('.,!?;"\'').lower() == word.lower()]

            if not songs:
                return None

            cache[word] = [song.to_dict() for song in songs]

            # Update the cache file
            save_song_cache(cache)

            return random.choice(songs)
        # No song exists for the word
        else:
            return None


def get_first_word_encoding_songs(message: str, sp: spotipy.Spotify) -> list[Song]:
    """Get a list of songs corresponding to the first words in the message."""
    songs = []

    for word in message.split():
        song = get_song_from_first_word(word.strip(), sp)
        if song:
            print(f"Found song: {song.name}")
            songs.append(song)
        else:
            raise Exception(f"No songs found for the word '{word}'.")

    return songs


def get_hex_encoding_songs(message: str, first_index: int = 5, second_index: int = 8) -> list[Song]:
    """Get a list of songs corresponding to the hex encoding of the message."""
    songs = []
    # Convert the message to its hexadecimal representation
    hex_message = message.encode("utf-8").hex()
    print(f"Hex message: {hex_message}")

    # Iterate byte by byte (2 hex characters) and check for songs with bytes in the corresponding track IDs indexes
    for byte in [hex_message[i:i+2] for i in range(0, len(hex_message), 2)]:
        with open("dataset.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            matched_songs = [row for row in reader if row['track_id'][first_index]
                             == byte[0] and row['track_id'][second_index] == byte[1]]

            # Found songs, save them
            if matched_songs:
                song_data = random.choice(matched_songs)
                song = Song(
                    track_id=song_data['track_id'],
                    name=song_data['track_name'],
                    spotify_url="https://open.spotify.com/track/" +
                    song_data['track_id']
                )
                print(f"Found song for byte '{byte}': {song.name}")
                songs.append(song)
            else:
                raise Exception(f"No songs found for the byte '{byte}'.")

    return songs


def get_message() -> str:
    """Prompt the user to enter a valid message."""
    while True:
        message = input("Enter the message to encode into songs: ")
        if message.strip():
            return message
        else:
            print("Message cannot be empty. Please try again.")


def get_encoding_method() -> str:
    """Prompt the user to choose an encoding method."""
    while True:
        encoding = input(
            "Choose encoding method - (1) First Word Encoding, (2) Hex Encoding: "
        ).strip()
        if encoding in ("1", "2"):
            return encoding
        else:
            print("Invalid choice. Please enter 1, 2, or leave blank for Hex Encoding.")


def get_playlist_url() -> str:
    """Prompt the user to enter a valid Spotify playlist URL."""
    while True:
        playlist_url = input(
            "Enter the Spotify playlist URL (leave blank for default): ").strip()
        if playlist_url == "":
            return "https://open.spotify.com/playlist/1qowu2b1APBPmn1kR8Ffju?si=ae2dab6cbc1b4fda"
        elif playlist_url.startswith("https://open.spotify.com/playlist/"):
            return playlist_url
        else:
            print("Invalid playlist URL. Please try again.")


def get_first_index() -> int:
    """Prompt the user to enter the first index for hex encoding."""
    while True:
        index = input(
            "Enter the first index for hex encoding (from 0 to 21) (default 5): ")
        if index == "":
            return 5
        elif index.isdigit():
            index = int(index)
            if index >= 0 and index <= 21:
                return index
            else:
                print("Index out of range. Please enter a number between 0 and 21.")


def get_second_index() -> int:
    """Prompt the user to enter the second index for hex encoding."""
    while True:
        index = input(
            "Enter the second index for hex encoding (from 0 to 21) (default 8): ")
        if index == "":
            return 8
        elif index.isdigit():
            index = int(index)
            if index >= 0 and index <= 21:
                return index
            else:
                print("Index out of range. Please enter a number between 0 and 21.")


if __name__ == "__main__":
    sp = authenticate_spotify()  # The main spotify client

    playlist_url = get_playlist_url()  # Get the playlist URL to save songs to

    # Extract the playlist ID from the URL
    playlist_id = playlist_url.split("/")[-1].split("?")[0]

    message = get_message()  # Get the message to encode
    encoding = get_encoding_method()  # Get the encoding method

    songs = []
    if encoding == "1":
        songs = get_first_word_encoding_songs(message, sp)
    elif encoding == "2" or encoding == "":
        first_index = get_first_index()
        second_index = get_second_index()
        songs = get_hex_encoding_songs(
            message, first_index=first_index, second_index=second_index)

    print("\nFinal song list:")
    print([song.name for song in songs])

    if songs:
        sp.playlist_replace_items(playlist_id, [])  # Clear existing items
        sp.playlist_add_items(playlist_id, [song.track_id for song in songs])
