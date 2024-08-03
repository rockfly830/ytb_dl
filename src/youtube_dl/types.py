from pydantic import BaseModel, Field, AliasChoices, AliasPath
from datetime import datetime

class Video(BaseModel):
    data: datetime
    title: str
    description: str
    channel_name: str
    playlist_id: str
    id: str
    thumbnail: str
    
    def toJSON(self):
        return {
            "data": self.data.timestamp(),
            "title": self.title,
            "description": self.description,
            "channel_name": self.channel_name,
            "playlist_id": self.playlist_id,
            "id": self.id
        }
    
    def __str__(self):
        return f"Video(name='{self.title}')"

    def __getitem__(self, item):
        return getattr(self, item)

class Playlist(BaseModel):
    id: str
    title: str
    videos_count: int
    thumbnail: str
    videos: list[Video] = []

    def toJSON(self):
        return {
            "id": self.id,
            "title": self.title,
            "videos_count": self.videos_count,
            "thumbnail": self.thumbnail,
        }
    
    def __str__(self):
        return f"Playlist(name='{self.title}')"

    def __getitem__(self, item):
        return getattr(self, item)
