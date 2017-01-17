class SentimentController < ApplicationController

  include SentimentHelper

  def search

    @tracks = SentimentHelper::Sentiment.lyrics_keywords(params[:word], params[:feeling])
    @feeling = params[:feeling]
#    @desired = params[:desired]

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
