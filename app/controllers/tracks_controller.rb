class TracksController < ApplicationController

  include TracksHelper

  def index

  end

  def search

    @tracks = TracksHelper::Track.lyrics_keywords(params[:word])
    analyzer = Sentimental.new
    # Load the default sentiment dictionaries
    analyzer.load_defaults

    # Set a global threshold
    analyzer.threshold = 1
    @valence = analyzer.score(params[:word])

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
