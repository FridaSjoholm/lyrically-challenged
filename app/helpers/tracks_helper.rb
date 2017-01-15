module TracksHelper

#Set up API Key:
  # (1) Include dotenv gem in your gem file (look at https://github.com/bkeepers/dotenv for instructions)
    # (1.a) Make ".env" file in the root of your project
    # (1.b) Include your API key as "MUSIC_GRAPH_API_KEY = "your key"

  #To use in a controller:
    # class SongsController < ApplicationController
    #   include MusicGraph

  #Sample call in your controller:
      # tracks = MusicGraph::Track.lyrics_keywords(params[:query])
      #tracks =[#<MusicGraph::Track:0x007fcb9df03cd0 @release_year=2012, @track_spotify_id="55h7vJchibLdUkxdlX3fK7", @popularity="0.871385", @title="Treasure", @artist_name="Bruno Mars", @duration=179>,...]

  class Track
    attr_reader :release_year, :title, :track_spotify_id, :popularity, :artist_name, :album_title, :lyrics

    API_URL = "http://api.musicgraph.com/api/v2/track/"

    def initialize(attributes)
      @release_year = attributes["release_year"]
      @track_spotify_id = attributes["track_spotify_id"]
      @popularity = attributes["popularity"]
      @title = ActiveSupport::Inflector.transliterate(attributes["title"])
      @artist_name = ActiveSupport::Inflector.transliterate(attributes["artist_name"])
      @duration = attributes["duration"]
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
      if params.is_a? String
        response = Faraday.get("#{API_URL}search?api_key=#{ENV['MUSIC_GRAPH_API_KEY']}&lyrics_keywords=#{params}")
      end
      tracks = JSON.parse(response.body)["data"]
      tracks.map { |attributes| new(attributes) }
    end

    def format_for_musixmatch
      self.title.split(" ").join("%20")
      self.title.delete("%20[Explicit%20Version]")
      self.title.delete("#%20[Explicit%20Version]")
      self.artist_name.split(" ").join("%20")
    end

    def lyrics
      JSON.parse(Net::HTTP.get(URI("https://api.musixmatch.com/ws/1.1/matcher.lyrics.get?format=json&callback=callback&q_track=#{self.title}&q_artist=#{self.artist_name}&apikey=" + ENV['MUSIXMATCH_API_KEY'])))
    end

    def format_for_lyrics_wikia
      self.artist_name.split(" ").join("_")
      self.title.split(" ").join("_")
      self.title.delete("_[Explicit_Version]")
    end

  end
end
