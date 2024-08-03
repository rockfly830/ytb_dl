from googleapiclient.discovery import build
from .types import Video, Playlist
from datetime import datetime
from loguru import logger

import os
import sys
import requests
import yt_dlp
import json

def get_highest_resolution(item):
    url = ""
    highest = 0
    for _, value in item['thumbnails'].items().__reversed__():
        current = value['width'] * value['height']
        if current > highest:
            highest = current
            url = value['url']

    return url

def extract_info_videos(items) -> list[Video]:
    infos = []
    for item in items:
        snippet = item["snippet"]
        try:
            data = datetime.strptime(snippet['publishedAt'].replace(" ", ""), "%Y-%m-%dT%H:%M:%SZ")

            infos.append(Video(**{
                    "data": data,
                    "title": snippet['title'],
                    "description": snippet['description'],
                    "channel_name": snippet['channelTitle'],
                    "playlist_id": snippet['playlistId'],
                    "id": snippet['resourceId']['videoId'],
                    "thumbnail": get_highest_resolution(snippet),
                }))

        except Exception as e:
            logger.error(f'Error extraction infos: {e}')
            print(item)
            exit()

    return infos

def extract_info_playlist(items) -> dict:
    infos = {}
    for item in items:
        try:
            info = Playlist(**{
                "id": item["id"],
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["maxres"]["url"],
                "videos_count": item["contentDetails"]["itemCount"]
            })

        except Exception as e:
            logger.error(f'Error extraction infos: {e}')
            exit()

        infos[item["snippet"]["title"]] = info

    return infos


class Youtube:
    _URL = "https://www.youtube.com/watch?v="

    def __init__(self, API_KEY: str, quiet: bool = False):
        self._quiet = quiet

        self._API_youtube = build('youtube', 'v3', developerKey=API_KEY)

        self._cache = {
            "channel_name": None,
            "channel_id": None,
            "upload_id": None,
            "playlist": {}
        }
        self._filters = []

        self._is_playlist_update = False
        self.__configure_logger()
        
    def __configure_logger(self):
        logger.remove()

        if self._quiet:
            return

        logger.add(sys.stdout, level="INFO"   , filter=lambda record: record["level"].name == "INFO"   )
        logger.add(sys.stdout, level="ERROR"  , filter=lambda record: record["level"].name == "ERROR"  )
        logger.add(sys.stdout, level="SUCCESS", filter=lambda record: record["level"].name == "SUCCESS")
        logger.add(sys.stdout, level="WARNING", filter=lambda record: record["level"].name == "WARNING")
        
        logger.add("infos.log"  , level="INFO"   , filter=lambda record: record["level"].name == "INFO"   )
        logger.add("error.log"  , level="ERROR"  , filter=lambda record: record["level"].name == "ERROR"  )
        logger.add("success.log", level="SUCCESS", filter=lambda record: record["level"].name == "SUCCESS")


    """ methods to handle a channel """
    def set_channel(self, name:str) -> str:
        self.get_channel_id(name)
        self.get_playlists()
        self.get_uploads_id()

        return self._cache["channel_id"]

    def get_channel_id(self, channel_name:str) -> str:
        if channel_name == self._cache.get("channel_name"):
            return self._cache["channel_id"]

        request = self._API_youtube.search().list(
            part='snippet',
            q=channel_name,
            type='channel',
            maxResults=1
        )
        response = request.execute()

        self._cache["channel_name"] = channel_name
        self._cache["channel_id"] = response['items'][0]['snippet']['channelId']

        return self._cache["channel_id"]


    """ playlists """
    def get_playlists(self) -> dict:
        if self._is_playlist_update:
            return self._cache["playlist"]

        request = self._API_youtube.playlists().list(
            part='snippet,contentDetails',
            channelId=self._cache["channel_id"]
        )
        response = request.execute()

        self._is_playlist_update = True
        self._cache["playlist"] = {"totalResults": response["pageInfo"]["totalResults"],
                "items": extract_info_playlist(response["items"])}

        return self._cache["playlist"]

    def get_uploads_id(self) -> str:
        if not self._cache.get("channel_id"):
            raise ValueError("You must set a channel!")

        if self._cache["upload_id"] is not None:
            return self._cache["upload_id"]

        channel_id = self._cache["channel_id"]

        request = self._API_youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()

        
        self._cache["upload_id"] = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        return self._cache["upload_id"]

    def get_videos_from_playlist(self, playlist_name: str) -> list[Video]:
        if not self._is_playlist_update:
            self.get_playlists()

        pl = self._cache["playlist"].get('items').get(playlist_name)
        
        if not pl:
            raise ValueError(f"Playlist '{playlist_name}' not found!")
            
        if pl.videos:
            return pl.videos

        videos = []
        next_page_token = None
        total_fetched = 0

        while True:
            try:
                request = self._API_youtube.playlistItems().list(
                    part='snippet',
                    playlistId=pl.id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                videos.extend(extract_info_videos(response['items']))

                total_fetched += len(response['items'])
                logger.info(f"fetched {total_fetched:^4} / {response['pageInfo']['totalResults']:^4}")

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            except Exception as e:
                logger.error(e)
                exit()

        pl.videos = videos
        return videos
    
    def get_videos_from_uploads(self) -> list[Video]:
        upload_id = self._cache["upload_id"]
            
        videos = []
        next_page_token = None
        total_fetched = 0

        while True:
            try:
                request = self._API_youtube.playlistItems().list(
                    part='snippet',
                    playlistId=upload_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                videos.extend(extract_info_videos(response['items']))

                total_fetched += len(response['items'])
                logger.info(f"fetched {total_fetched:^4} / {response['pageInfo']['totalResults']:^4}")

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            except Exception as e:
                logger.error(e)
                exit()


        return videos


    """ download videos """
    def _donwload_thumbnail(self, url:str, filename:str) -> bool:
        try:
            filename = filename + ".jpg"
            
            response = requests.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to download thumbnail {url}, status code {response.status_code}") 
                return False

            with open(filename, "wb") as f:
                f.write(response.content)

        except Exception as e:
            logger.error(e)
            exit()

        return True

    def download_video(self, id:str, output_path:str, thumb_path:str = "") -> None:
        ydl_opts = {
            'quiet': True,
            'ignoreerrors': True,
            "no_warnings": True,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(self._URL + id)

                if self._download_thumbnail:
                    filename = os.path.join(thumb_path, f"{id}_thumb")
                    self._donwload_thumbnail(result['thumbnail'], filename)

        except Exception as e:
            logger.error(e)
            exit()

    def _download_videos(self, videos:list[Video], output_path:str) -> None:
        output_path = output_path.replace(" ", "")
        os.makedirs(output_path, exist_ok=True)

        if self._donwload_thumbnail:
            thumb_path = os.path.join(output_path, "thumb")
            os.makedirs(thumb_path, exist_ok=True)
        else:
            thumb_path = ""
        
        try:
            total = len(videos)
            for index, video in enumerate(videos, start=1):
                self.download_video(video.id, output_path, thumb_path)

                logger.success(f"download '{video.title.split('-')[0][:30]}' {index} / {total}")


        except Exception as e:
            logger.error(e)
            exit()
    
    def download_all(self, output_path:str = "videos", download_thumbnail:bool = False) -> None:
        self._download_thumbnail = download_thumbnail
        
        videos = self.get_videos_from_uploads()

        videos = self._filter_videos(videos)

        logger.info("downloading all videos")
        self._download_videos(videos, output_path)

    def download_playlist(self, playlist_name:str, output_path:str = "videos", download_thumbnail:bool = False) -> None:
        self._download_thumbnail = download_thumbnail
        
        videos = self.get_videos_from_playlist(playlist_name)

        videos = self._filter_videos(videos)

        logger.info(f"downloading videos from '{playlist_name}' playlist")
        self._download_videos(videos, output_path)


    """ filter """
    def _should_download(self, item:dict) -> bool:
        if len(self._filters) == 0:
            return True
            
        for filt in self._filters:
            if filt(item):
                return True
                
        return False

    def set_filter(self, video_filter:callable) -> None:
        """
            The filter argument is a Video instance
            
            Use the following attributes to filter the videos:
            
            data: date of video publish
            title: video title
            description: video description
            channel_name: channel name who publish the video
            playlist_id: playlist id where the video was fetch
            id: video id
        """
        self._filters.append(video_filter)

    def _filter_videos(self, videos:list[Video]) -> list[Video]:
        return [video for video in videos if self._should_download(video)]
