module TracksHelper

#Set up API Key:
  # (1) Include dotenv gem in your gem file (look at https://github.com/bkeepers/dotenv for instructions)
    # (1.a) Make ".env" file in the root of your project
    # (1.b) Include your API key as "MUSIC_GRAPH_API_KEY = "your key"

  #To use in a controller:
    # class SongsController < ApplicationController
    #   include TracksHelper

  #Sample call in your controller:
      # tracks = TracksHelper::Track.lyrics_keywords(params[:query])
      #tracks =[#<TracksHelper::Track:0x007fcb9df03cd0 @release_year=2012, @track_spotify_id="55h7vJchibLdUkxdlX3fK7", @popularity="0.871385", @title="Treasure", @artist_name="Bruno Mars", @duration=179>,...]

  class Track
    attr_reader :release_year, :title, :track_spotify_id, :popularity, :artist_name, :album_title, :lyrics, :audio_features

    API_URL = "http://api.musicgraph.com/api/v2/track/"

    def initialize(attributes)
      #[MusicGraph] these attributes from MusicGraph
      @release_year = attributes["release_year"]
      @track_spotify_id = attributes["track_spotify_id"]
      @popularity = attributes["popularity"]
      @title = attributes["title"]
      @artist_name = attributes["artist_name"]
      @duration = attributes["duration"]

      #[Lyricfy] Get lyrics, set to nil if error
      begin
        @lyrics = get_lyrics(format_for_lyrics_wikia(attributes["title"], attributes["artist_name"]))
      rescue ArgumentError => e
        @lyrics = nil
      end

      #[RSpotify] Get audio_features for track
        #audio_features include :valence, :danceability, :duration_ms, :energy, :instrumentalness, :liveness, :speechiness, :tempo, :time_signature, :mode
      @audio_features = RSpotify::AudioFeatures.find(attributes["track_spotify_id"])
      p @audio_features
    end

    #Find tracks by a given keyword, initialize new tracks with attrs
    def self.lyrics_keywords(params, limit=12) #TD: RENAME - self.get_tracks_by_keyword
      p "LIMIT IS"
      p limit
      sanitized_string = params.gsub("'","")
      if params.is_a? String
        response = Faraday.get("#{API_URL}search?api_key=#{ENV['MUSIC_GRAPH_API_KEY']}&limit=#{limit}&lyrics_keywords=#{sanitized_string}")
      end
      tracks = JSON.parse(response.body)["data"]
      clean_tracks = clean_and_prepare_track_data(tracks)
      clean_tracks.map { |attributes| new(attributes) }
    end

    #Only display tracks that have valid spotify id's
    def self.clean_and_prepare_track_data(tracks)
      tracks.select { |track| track.key?("track_spotify_id") }
    end

    #For 02_sentiment madlib
    #Filter by matching given feeling
    def match_sentiment(form_feeling)
        if form_feeling == "sad"
          p "You want to be sad"
          audio_features.valence < 0.4
        elsif form_feeling == "angry"
          p "You want to be angry"
          audio_features.valence >= 0.4 && audio_features.valence <= 0.6
        elsif form_feeling == "calm"
          p "You want to be calm"
          audio_features.valence > 0.4 && audio_features.tempo < 100
        elsif form_feeling == "happy"
          p "You want to be happy"
          audio_features.valence > 0.6
        end
      end


      def format_for_lyrics_wikia(title, artist_name)
        title = ActiveSupport::Inflector.transliterate(title)
        title_arr = title.split(" ")
        title = title_arr.join("_")
        title = title.delete("#")
        title = title.gsub(/_?\[(.*?)\]/, "")

        artist_name = ActiveSupport::Inflector.transliterate(artist_name)
        artist_arr = artist_name.split(" ")
        artist_arr.map(&:capitalize!)
        artist_name = artist_arr.join("_")
        artist_name = URI.escape(artist_name, /[?#]/)
        return {title:title, artist_name: artist_name}
      end

      #[Lyricfy] Lyricfy gets lyrics from LyricsWikia or MetroMix
      def get_lyrics(args)
        fetcher = Lyricfy::Fetcher.new
        x = args[:artist_name]
        y = args[:title]
        song = fetcher.search(x, y)
        begin
          if song
            song.body("\n")
          else
            return "Lyric not found"
          end
        rescue NoMethodError => e
          return "Lyric not found"
        end
      end

      #For 02_sentiment madlib
      #Filter by matching given feeling
      def match_weather(want_to)
        if want_to == "dance"
          audio_features.valence > 0.5 && audio_features.danceability > 0.5
        elsif want_to == "chill"
          audio_features.valence > 0.5 && audio_features.danceability < 0.5
        elsif want_to == "sulk"
          audio_features.valence < 0.5 && audio_features.energy < 0.6
        elsif want_to == "rage"
          audio_features.valence < 0.5 && audio_features.energy > 0.5
        end
      end


  end#for Class
end#for Module
