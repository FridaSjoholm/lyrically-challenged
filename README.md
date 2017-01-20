
![Lyrically Challenged](https://github.com/FridaSjoholm/lyrically-challenged/blob/development/app/assets/images/LClogo.png?raw=true)
Team: Katie, Katrina, Jin, Christian, Frida

Search for songs by lyrics.
---
The site is available live on [Heroku](http://lyricallychallenged.herokuapp.com/)

---
##To clone the repo for localhost:

### [0] Clone the repo

In your terminal, navigate to where you want to place the file:
```bash
  git clone https://github.com/FridaSjoholm/lyrically-challenged.git
```

### [1] Get (and hide) your API keys

#### Include dotenv gem in your gem file (look at https://github.com/bkeepers/dotenv for instructions)

####You'll need to get API keys from:
-MusicGraph
-Spotify
-api.ai
-Google NL

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

### [2] Navigate to the project 
-Navigate to the project
-Run bundle to install gems
-Start the rails server

```bash
  cd lyricallychallenged
  bundle
  rails s
````



