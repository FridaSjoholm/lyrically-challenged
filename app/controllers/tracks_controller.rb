class TracksController < ApplicationController

  def index
    @word = "coffee"
    url = "http://api.musicgraph.com/api/v2/track/search?api_key=" + ENV['MUSIC_GRAPH_API_KEY'] + "&lyrics_phrase=" + @word
    uri = URI(url)
    response = Net::HTTP.get(uri)
    @tracks = JSON.parse(response)

    # happy_api_call = JSON.parse(Net::HTTP.get(URI("http://api.musicgraph.com/api/v2/track/search?api_key=1aeb0c665ce5e2a00bf34da9ec035877&lyrics_phrase=" + @word)))
    # @tracks = happy_api_call
  end

end
