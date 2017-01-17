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
    attr_reader :release_year, :title, :track_spotify_id, :popularity, :artist_name, :album_title, :lyrics, :genre, :track_youtube_id :audio_features

    API_URL = "http://api.musicgraph.com/api/v2/track/"

    def initialize(attributes)
      @release_year = attributes["release_year"]
      @track_spotify_id = attributes["track_spotify_id"]
      @popularity = attributes["popularity"]
      @title = ActiveSupport::Inflector.transliterate(attributes["title"])
      @artist_name = ActiveSupport::Inflector.transliterate(attributes["artist_name"])
      @duration = attributes["duration"]
      @genre = attributes["main_genre"]
      @track_youtube_id = attributes['track_youtube_id']


      @audio_features = RSpotify::AudioFeatures.find(attributes["track_spotify_id"])
      #audio_features include :valence, :danceability, :duration_ms, :energy, :instrumentalness, :liveness, :speechiness, :tempo, :time_signature, :mode
    end

    def self.search(params)
      if params.is_a? String
        response = Faraday.get("#{API_URL}search?api_key=#{ENV['MUSIC_GRAPH_API_KEY']}&title=#{params}")
      elsif params.is_a? Hash
        encoded_params = URI.encode_www_form(params)
        response = Faraday.get("#{API_URL}search?api_key=#{ENV['MUSIC_GRAPH_API_KEY']}&#{encoded_params}")
      end
      tracks = JSON.parse(response.body)["data"]
      tracks.map { |attributes| new(attributes) }
    end

    def self.lyrics_keywords(params)
      sanitized_string = params.gsub("'","")
      if params.is_a? String
        response = Faraday.get("#{API_URL}search?api_key=#{ENV['MUSIC_GRAPH_API_KEY']}&limit=12&lyrics_keywords=#{sanitized_string}")
      end
      tracks = JSON.parse(response.body)["data"]
      tracks.map { |attributes| new(attributes) }
    end


    def lyrics
      fetcher = Lyricfy::Fetcher.new
      begin
        if fetcher.search @artist_name, @title
          song = fetcher.search @artist_name, @title
          song.body("\n")

        else
          return "Lyric not found"
        end
      rescue NoMethodError => e
        return "Lyric not found"
      end
    end

    def format_for_lyrics_wikia
      title_arr = @title.split(" ")
      @brantitle = title_arr.join("_")
      @title = @title.delete("#")
      @title = @title.gsub(/_?\[(.*?)\]/, "")
      artist_arr = @artist_name.split(" ")
      artist_arr.map(&:capitalize!)
      @artist_name = artist_arr.join("_")
      @artist_name = URI.escape(@artist_name, /[?#]/)
    end

  end
end
