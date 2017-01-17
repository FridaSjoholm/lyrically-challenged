class SentimentController < ApplicationController

  include TracksHelper

  def search

    #PARAMS

    #User choose feeling on form
    @form_feeling = params[:feeling]
    #Get tracks which match the sentiment of the form_feeling
    @tracks = TracksHelper::Track.lyrics_keywords(params[:word], 20).select{ |t| t.match_sentiment(@form_feeling)}

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
