class DemosController < ApplicationController

  def index
    #Sample call to Spotify

    # #Happy by Pharrel Williams, spotify_id = "6NPVjNh8Jhru9xOmyQigds"

    #Check RSpotify is making a successful call
     @track = RSpotify::Track.find("6NPVjNh8Jhru9xOmyQigds")
     p "track is found" if @track != nil

    #Get audio features for this track
    p audio_features = RSpotify::AudioFeatures.find('6NPVjNh8Jhru9xOmyQigds')
    @valence = audio_features.valence
    @danceability = audio_features.danceability
    @duration_ms = audio_features.duration_ms
    @energy = audio_features.energy
    @instrumentalness = audio_features.instrumentalness
    @liveness = audio_features.liveness
    @speechiness = audio_features.speechiness
    @tempo = audio_features.tempo
    @time_signature = audio_features.time_signature

    #See all audio_features here
    #https://developer.spotify.com/web-api/get-audio-features/
  end
end
