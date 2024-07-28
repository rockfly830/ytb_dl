from dotenv import load_dotenv

from youtube_dl import Youtube
import os

if __name__ == "__main__":
    load_dotenv()
    
    API_KEY = os.getenv("API_KEY")

    CHANNEL_NAME = 'Google'

    youtube = Youtube(API_KEY)

    youtube.set_channel(CHANNEL_NAME)

    playlists = youtube.get_playlists().items

    first_playlist = playlists[0].title

    youtube.download_playlist(playlist_name=first_playlist,
                                output_path=f"./videos/{first_playlist}", 
                                download_thumbnail=True)
