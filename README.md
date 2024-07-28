# YouTube downloader

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)

## About <a name = "about"></a>

YouTube downloader lets you downloader videos from youtube easely.

## Getting Started <a name = "getting_started"></a>


### Prerequisites

This project needs google client and yt-dlp to works properlly. 

### Installing

clone this repository.

```
git clone https://github.com/rockfly830/you_dl.git
```

and install

```
pip install .
```

## Usage <a name = "usage"></a>

```
    from dotenv import load_dotenv
    from youtube_dl import Youtube
    import os

    # you need google api key
    API_KEY = os.getenv("API_KEY")
    
    CHANNEL_NAME = 'Google'

    youtube = Youtube(API_KEY)

    youtube.set_channel(CHANNEL_NAME)

    # To download all playlist, it is not necessary to save the return
    playlists = youtube.get_playlists().items

    first_playlist = playlists[0].title

    youtube.download_playlist(playlist_name=first_playlist,
                                output_path=f"./videos/{first_playlist}", 
                                download_thumbnail=True)

```
