import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from models import Song


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
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotifycache",
    )

    # Setup the main spotify object
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


def get_encoding_method() -> str:
    """Prompt the user to choose an encoding method."""
    while True:
        encoding = input(
            "Choose encoding method used in the playlist - (1) First Word Encoding, (2) Hex Encoding: "
        ).strip()
        if encoding in ("1", "2"):
            return encoding
        else:
            print("Invalid choice. Please enter 1 or 2.")


def get_playlist_url() -> str:
    """Prompt the user to enter a valid Spotify playlist URL."""
    while True:
        playlist_url = input(
            "Enter the Spotify playlist URL (leave blank for default): "
        ).strip()
        if playlist_url == "":
            return "https://open.spotify.com/playlist/1qowu2b1APBPmn1kR8Ffju?si=ae2dab6cbc1b4fda"
        elif playlist_url.startswith("https://open.spotify.com/playlist/"):
            return playlist_url
        else:
            print("Invalid playlist URL. Please try again.")


def get_songs_from_playlist(sp: spotipy.Spotify, playlist_url: str) -> list[Song]:
    """Fetch all songs from the given playlist URL and return them as Song objects."""
    # Extract playlist ID from the URL
    playlist_id = playlist_url.split("/")[-1].split("?")[0]

    songs: list[Song] = []

    results = sp.playlist_items(playlist_id)
    while results:
        for item in results["items"]:
            track = item.get("track")
            if not track:
                continue

            track_id = track.get("id")
            name = track.get("name")
            external_urls = track.get("external_urls") or {}
            spotify_url = external_urls.get("spotify", "")

            if track_id and name:
                song = Song(
                    track_id=track_id,
                    name=name,
                    spotify_url=spotify_url,
                )
                songs.append(song)

        if results.get("next"):
            results = sp.next(results)
        else:
            results = None

    return songs


def decode_first_word_encoding(songs: list[Song]) -> str:
    """Decode a message from songs using the First Word encoding scheme."""
    words: list[str] = []

    for song in songs:
        if not song.name:
            continue

        first_word = song.name.split()[0].strip('.,!?;"\'')
        if first_word:
            words.append(first_word)

    return " ".join(words)


def decode_hex_encoding(
    songs: list[Song],
    first_index: int = 5,
    second_index: int = 8,
) -> str:
    """Decode a message from songs using the Hex encoding scheme."""
    hex_bytes: list[str] = []

    for song in songs:
        track_id = song.track_id

        # Safety check in case playlist was modified
        if len(track_id) <= max(first_index, second_index):
            raise Exception(
                f"Track ID '{track_id}' is too short to contain indices "
                f"{first_index} and {second_index}."
            )

        byte = track_id[first_index] + track_id[second_index]
        hex_bytes.append(byte)

    hex_string = "".join(hex_bytes)

    try:
        decoded_bytes = bytes.fromhex(hex_string)
        message = decoded_bytes.decode("utf-8")
    except ValueError as e:
        raise Exception(
            f"Failed to decode hex string '{hex_string}': {e}"
        ) from e

    return message


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
    sp = authenticate_spotify()  # The main Spotify client

    playlist_url = get_playlist_url()  # Playlist to read from
    encoding = get_encoding_method()   # Encoding scheme used

    songs = get_songs_from_playlist(sp, playlist_url)

    print("\nSongs found in playlist (in order):")
    print([song.name for song in songs])

    if not songs:
        print("\nNo songs found in the playlist.")
        exit(0)

    if encoding == "1":
        message = decode_first_word_encoding(songs)
    elif encoding == "2":
        first_index = get_first_index()
        second_index = get_second_index()
        message = decode_hex_encoding(
            songs, first_index=first_index, second_index=second_index)
    else:
        # Should never happen due to validation in get_encoding_method
        raise Exception("Unknown encoding method.")

    print("\nDecoded message:")
    print(message)
