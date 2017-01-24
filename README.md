
![Lyrically Challenged](https://github.com/FridaSjoholm/lyrically-challenged/blob/development/app/assets/images/LClogo.png?raw=true)

####Search for songs by lyrics.

## Description 
LyricallyChallenged is a lyric-based Rails app and [iOS app](https://github.com/FridaSjoholm/Lycheee) to search for songs.  Each song can be played via a Spotify widget and is presented with full lyrics and details on why that song was chosen. 

Recent [research](https://www.cse.unr.edu/~mgunes/papers/ComNet16Lyric.pdf) indicates that lyric-based recommendatation systems are 12.6 times more effective than random recommendations, and may offer better recommendations than collaborative filtering, esepcially "within small musical niches".

##Usage
* Visit the LyricallyChallenged main page and search for songs by keyword(s)
![](https://media.giphy.com/media/y6tNjPEAn7eaA/giphy.gif)

* Each song is displayed with a Spotify widget and full lyrics
![](https://media.giphy.com/media/ODhZk2POEhilG/giphy.gif)

---
The site is available live on [Heroku](http://lyricallychallenged.herokuapp.com/)

---
#To clone the repo for localhost:

### 0. Clone the repo

In your terminal, navigate to where you want to place the file:
```bash
  git clone https://github.com/FridaSjoholm/lyrically-challenged.git
```

### 1. Get (and hide) your API keys

#### 2. Include dotenv gem in your gem file (look at https://github.com/bkeepers/dotenv for instructions)

####You'll need to get API keys from:
- [MusicGraph](https://developer.musicgraph.com/)
- [Spotify](https://developer.spotify.com/web-api/)
- [api.ai](https://docs.api.ai/)
- [Google Natural Language](https://cloud.google.com/natural-language/)

#### .env file
This is what our .env file looks like, with the empty strings replaced with API keys.

```bash
SPOTIFY_API_OAUTH_KEY = ""
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
MUSIC_GRAPH_API_KEY = ""
GOOGLE_APPLICATION_CREDENTIALS = "".json
```
* The GOOGLE_APPLICATION_CREDENTIALS will be a path file to a json file in the root of your app.

### 3. Navigate to the project 
-Navigate to the project
-Run bundle to install gems
-Start the rails server

```bash
  cd lyricallychallenged
  bundle
  rails s
```
🎉 🎉 Yay! Your site will probably be live at http://localhost:3000/
---

## About Lyrically Challenged
__See our presentation deck [here](https://docs.google.com/presentation/d/18gs0EuPftq-oOJ0Y8CxVBfq1NHgCIdqfTmrZaZVhhj0/edit#slide=id.g1c13a4db47_0_36)__
This project was created in our 19th week at Dev Bootcamp, and was built using Rails, HTML/CSS, and Javascript.  We used the Spotify, MusicGraph, api.ai, MetroMix, and Google Natural Language APIs.

## Contributors

* [Katie O'Neil](https://github.com/katieboundary)
* [Katrina DeVaney](https://github.com/kattak)
* [Jin Di Giordano](https://github.com/jindigiordano)
* [Christian Salas](https://github.com/SalasC2)
* [Frida Sjöholm](https://github.com/FridaSjoholm)

If you are interested in improving or adding new awesome features to LyricallyChallenged, please feel free to submit an issue or pull request!

