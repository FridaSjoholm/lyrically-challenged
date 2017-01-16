class DemosController < ApplicationController

  def index
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
    analyzer = Sentimental.new
    # Load the default sentiment dictionaries
    analyzer.load_defaults

    # Set a global threshold
    analyzer.threshold = 1
    @valence = analyzer.score(params[:word])

    respond_to do |format|
      if @tracks.length > 0
        @songs = []
        @tracks.each do |track|
          if track.track_spotify_id != nil
            song = RSpotify::AudioFeatures.find(track.track_spotify_id)
            if song.valence < 0.3 && @valence < -(0.5)
              @songs << track
            elsif song.valence > 0.3 && @valence > -(0.5)
              @songs << track
            end
          else
            if @valence < -(0.5)
              @songs << track
            elsif @valence > -(0.5)
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
