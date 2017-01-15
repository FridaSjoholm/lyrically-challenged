class DemosController < ApplicationController

  def index
    #Sample call to Spotify
   # #Happy by Pharrel Williams


   #Check RSpotify is making a successful call
        # track = RSpotify::Track.find("6NPVjNh8Jhru9xOmyQigds")
        # p "track is found" if track != nil



   #Attempt 0: Try with Track.find
    # track = RSpotify::Track.find("6NPVjNh8Jhru9xOmyQigds")
    # p "track is found" if track != nil
    # p track.audio_features
    # p track.audio-features

   #Attempt 1: Try with Track.search
  #  track = RSpotify::Track.search(track.name).first
  #  p track
  #  track.audio-features
  #  track.audio_features

   #Attempt 2: Try with RSpotify::AudioFeatures.find
  #  p audio-features = RSpotify::AudioFeatures.find('6NPVjNh8Jhru9xOmyQigds')
  #  p audio-features.valence
  end
end
