from dotenv import load_dotenv

from youtube_dl.youtube_dl import Youtube
from datetime import datetime
import os

if __name__ == "__main__":
    load_dotenv()
    
    API_KEY = os.getenv("API_KEY")

    CHANNEL_NAME = ''

    youtube = Youtube(API_KEY)

    youtube.set_channel(CHANNEL_NAME)

    youtube.set_filter(lambda x: x.data >= datetime(2024, 7, 28))

    youtube.download_all(output_path=f"./videos/{CHANNEL_NAME}", 
                                download_thumbnail=True)
