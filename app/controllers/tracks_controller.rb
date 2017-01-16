class TracksController < ApplicationController

  include TracksHelper

  def index

  end

  def search

    @tracks = TracksHelper::Track.lyrics_keywords(params[:word])
    p "HITTING tracks#search"
    p @tracks.first
    # @word = params[:word]
    # url = "http://api.musicgraph.com/api/v2/track/search?api_key=" + ENV['MUSIC_GRAPH_API_KEY'] + "&lyrics_phrase=" + @word
    # uri = URI(url)
    # response = Net::HTTP.get(uri)
    # @tracks = JSON.parse(response)

    respond_to do |format|
      if @tracks.length > 0
        format.html {render :show, layout: false}
      else
        flash[:danger] = 'There was a problem'
        format.html { render :index }
        format.json { }
      end
    end

  end
end
