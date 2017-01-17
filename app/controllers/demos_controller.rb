class DemosController < ApplicationController

  def index
    require 'googleauth'
    # Get the environment configured authorization
    scopes =  ['https://www.googleapis.com/auth/cloud-platform',
               'https://www.googleapis.com/auth/compute']
    authorization = Google::Auth.get_application_default(scopes)

    # Add the the access token obtained using the authorization to a hash, e.g
    # headers.
    some_headers = {}
    authorization.apply(some_headers)

    require "google/cloud/language"

    # language = Google::Cloud::Language.new

    # content = "Star Wars is a great movie. The Death Star is fearsome."
    # document = language.document content
    # annotation = document.annotate
    #
    # p annotation.entities.count #=> 3
    # p annotation.sentiment.score #=> 0.10000000149011612
    # p annotation.sentiment.magnitude #=> 1.100000023841858
    # p annotation.sentences.count #=> 2
    # p annotation.tokens.count #=> 13

    # #Sample call to Spotify
    #
    # # #Happy by Pharrel Williams, spotify_id = "6NPVjNh8Jhru9xOmyQigds"
    #
    # #Check RSpotify is making a successful call
    #  @track = RSpotify::Track.find("6NPVjNh8Jhru9xOmyQigds")
    #  p "track is found" if @track != nil
    #
    # #Get audio features for this track
    # p audio_features = RSpotify::AudioFeatures.find('6NPVjNh8Jhru9xOmyQigds')
    # @valence = audio_features.valence
    # @danceability = audio_features.danceability
    # @duration_ms = audio_features.duration_ms
    # @energy = audio_features.energy
    # @instrumentalness = audio_features.instrumentalness
    # @liveness = audio_features.liveness
    # @speechiness = audio_features.speechiness
    # @tempo = audio_features.tempo
    # @time_signature = audio_features.time_signature

    #See all audio_features here
    #https://developer.spotify.com/web-api/get-audio-features/
  end

  def search
    @tracks = TracksHelper::Track.lyrics_keywords(params[:word])
    language = Google::Cloud::Language.new
    content = @tracks
    document = language.document content
    annotation = document.annotate

    # # p annotation.entities.count
    # p "ANNOTATION ENTITIES"
    # p annotation.entities
    #
    # p "ANNOTATION SENTIMENT SCORE"
    # p annotation.sentiment.score
    #
    # p "ANNOTATION SENTIMENT MAGNITUDE"
    # p annotation.sentiment.magnitude
    # # p annotation.sentences.count

    respond_to do |format|
      if @tracks.length > 0
        @songs = []
        @tracks.each do |track|
          if track.track_spotify_id != nil
            song = RSpotify::AudioFeatures.find(track.track_spotify_id)

            if song.valence < 0.2 && annotation.sentiment.score < -(0.4)
              @songs << track
            elsif (song.valence > 0.2 && song.valence < 0.4) && (annotation.sentiment.score < 0 && annotation.sentiment.score > -(0.4))
              @songs << track
            elsif (song.valence > 0.4 && song.valence < 0.6) && (annotation.sentiment.score < 0.5 && annotation.sentiment.score > 0)
              @songs << track
            elsif (song.valence > 0.6 && song.valence <= 1) && (annotation.sentiment.score > 0.5 && annotation.sentiment.score <= 1)
              @songs << track
            end
          else
            if annotation.sentiment.score < -(0.4)
              @songs << track
            elsif annotation.sentiment.score < 0 && annotation.sentiment.score > -(0.4)
              @songs << track
            elsif annotation.sentiment.score < 0.5 && annotation.sentiment.score > 0
              @songs << track
            elsif annotation.sentiment.score <= 1 && annotation.sentiment.score > 0.5
              @songs << track
            end
          end
        end
        format.html {render :show, layout: false}
      else
        flash[:danger] = 'There was a problem'
        format.html { render :index }
        format.json { }
      end
    end
  end
end
