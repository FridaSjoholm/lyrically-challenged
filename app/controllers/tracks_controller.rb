class TracksController < ApplicationController

  def index
    @word = "coffee"
    url = "http://api.musicgraph.com/api/v2/track/search?api_key=" + ENV['MUSIC_GRAPH_API_KEY'] + "&lyrics_phrase=" + @word
    uri = URI(url)
    response = Net::HTTP.get(uri)
    @tracks = JSON.parse(response)

    #Sample RSpotify call
    my_tracks = RSpotify::Track.find("3YuaBvuZqcwN3CEAyyoaei")

    p "*"* 80
    p my_tracks
    p "*"* 80

  end

end
