class Song:
    def __init__(self, track_id: str, name: str, spotify_url: str):
        self.track_id = track_id
        self.name = name
        self.spotify_url = spotify_url

    def to_dict(self):
        return {
            "track_id": self.track_id,
            "name": self.name,
            "spotify_url": self.spotify_url
        }
