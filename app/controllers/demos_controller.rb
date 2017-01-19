class DemosController < ApplicationController

  def index
    # require 'googleauth'
    # # Get the environment configured authorization
    # scopes =  ['https://www.googleapis.com/auth/cloud-platform',
    #            'https://www.googleapis.com/auth/compute']
    # authorization = Google::Auth.get_application_default(scopes)
    #
    # # Add the the access token obtained using the authorization to a hash, e.g
    # # headers.
    # some_headers = {}
    # authorization.apply(some_headers)
    #
    # require "google/cloud/language"
    #
    # language = Google::Cloud::Language.new
    #
    # content = "Stupid api doesn't even work"
    # document = language.document content
    # annotation = document.annotate
    #
    # p annotation.sentences[0]

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
    # @key
    # @mode
    #

    #See all audio_features here
    #https://developer.spotify.com/web-api/get-audio-features/
  end

  # def search
  #   p "Something random " * 100
  #   if request.xhr?
  #     p params
  #     p "Ajax stuff"
  #   end
  # end

  # def search
  #   language = Google::Cloud::Language.new
  #
  #   content = "spe"
  #   document = language.document content
  #   annotation = document.annotate
  #
  #   score = annotation.sentiment.score
  #   p score
  #
  #   if score <= -(0.4)
  #      word = "depressing"
  #   elsif score <= 0 && score >= -(0.4)
  #      word = "sad"
  #   elsif score <= 0.5 && score >= 0
  #      word = "okay"
  #   elsif score <= 1 && score >= 0.5
  #      word = "happy"
  #   end
  #
  #   @tracks = TracksHelper::Track.lyrics_keywords(word, 20)
  #   respond_to do |format|
  #     if @tracks.length > 0
  #       format.html {render :show, layout: false}
  #       format.json {render json: @tracks.map{|track| track.as_json.slice("title", "artist_name", "track_spotify_id")}}
  #     else
  #       flash[:danger] = 'There was a problem'
  #       format.html { render :_no_results, layout: false }
  #       format.json { }
  #     end
  #   end
  # end
end
