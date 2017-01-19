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
    attr_reader :release_year, :title, :track_spotify_id, :popularity, :artist_name, :album_title, :lyrics, :genre, :track_youtube_id, :audio_features


    API_URL = "http://api.musicgraph.com/api/v2/track/"

    def initialize(attributes)
      #[MusicGraph] these attributes from MusicGraph
      @release_year = attributes["release_year"]
      @track_spotify_id = attributes["track_spotify_id"]
      @popularity = attributes["popularity"]
      @title = attributes["title"]
      @artist_name = attributes["artist_name"]
      @duration = attributes["duration"]
      @genre = attributes["main_genre"]
      @track_youtube_id = attributes['track_youtube_id']

      if attributes["main_genre"] == nil
        @genre = "no genre found"
      end

      @audio_features = RSpotify::AudioFeatures.find(attributes["track_spotify_id"])
      #audio_features include :valence, :danceability, :duration_ms, :energy, :instrumentalness, :liveness, :speechiness, :tempo, :time_signature, :mode

      #[Lyricfy] Get lyrics, set to nil if error
      begin
        @lyrics = get_lyrics(format_for_lyrics_wikia(attributes["title"], attributes["artist_name"]))
      rescue ArgumentError => e
        @lyrics = "Lyrics not found"
      end

      #[RSpotify] Get audio_features for track
        #audio_features include :valence, :danceability, :duration_ms, :energy, :instrumentalness, :liveness, :speechiness, :tempo, :time_signature, :mode
      @audio_features = RSpotify::AudioFeatures.find(attributes["track_spotify_id"])
    end

    #Find tracks by a given keyword, initialize new tracks with attrs
    def self.lyrics_keywords(params, limit=12, genre="", offset="") #TD: RENAME - self.get_tracks_by_keyword
      sanitized_string = params.gsub("'","")

      # if genre, get and sanitize
      if genre != ""
        genre_url = "&genre=#{genre}"
      end

      if offset != ""
        offset_url = "&offset=#{offset}"
      end

      if params.is_a? String
        response = Faraday.get("#{API_URL}search?api_key=#{ENV['MUSIC_GRAPH_API_KEY']}&limit=#{limit}&lyrics_keywords=#{sanitized_string}" + "#{genre_url}" + "#{offset_url}")

      end
      tracks = JSON.parse(response.body)["data"]
      clean_tracks = clean_and_prepare_track_data(tracks)
      # byebug
      clean_tracks.map { |attributes| Track.new(attributes) }
    end

    #Only display tracks that have valid spotify id's
    def self.clean_and_prepare_track_data(tracks)
      tracks.select { |track| track.key?("track_spotify_id") }
    end

    #For 02_sentiment madlib
    #Filter by matching given feeling
    def match_sentiment(form_feeling)
        if form_feeling == "sad"
          audio_features.valence < 0.4
        elsif form_feeling == "angry"
          audio_features.valence >= 0.4 && audio_features.valence <= 0.6
        elsif form_feeling == "calm"
          audio_features.valence > 0.4 && audio_features.tempo < 100
        elsif form_feeling == "happy"
          audio_features.valence > 0.6
        end
    end

    #Helper method for tracking your feelings in a day form
    def feelings_day(feelings, day)
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
      # language = Google::Cloud::Language.new
      # content = feelings
      # document = language.document content
      # annotation = document.annotate

      # if annotation.sentiment.score < -(0.4)
      #    audio_features.valence < convert_google_sentiment_to_spotify_valence(-0.4)
      # elsif (annotation.sentiment.score < 0 && annotation.sentiment.score > -(0.4))
      #   p "sad"
      # elsif (annotation.sentiment.score < 0.5 && annotation.sentiment.score > 0)
      #   p "Sort of happu"
      # elsif (annotation.sentiment.score > 0.5 && annotation.sentiment.score <= 1)
      #   p "HAppy "
      # else
      #   p "ooppss"
      # end

      # return (audio_features.valence < convert_google_sentiment_to_spotify_valence(annotation.sentiment.score) + 0.5) && (audio_features.valence > convert_google_sentiment_to_spotify_valence(annotation.sentiment.score) - 0.5)

    end

    def convert_google_sentiment_to_spotify_valence(gsentiment)
      return 0.5 + (gsentiment/2)
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
        begin
          fetcher = Lyricfy::Fetcher.new
          p x = args[:artist_name]
          p y = args[:title]
          song = fetcher.search(x, y) if fetcher
        rescue NoMethodError => e
          return "Lyric not found"
        end

        begin
          if song
            song.body("\n")
          else
            return "Lyrics not found"
          end
        rescue NoMethodError => e
          return "Lyrics not found"
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
