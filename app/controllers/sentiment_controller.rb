class SentimentController < ApplicationController

  include SentimentHelper

  def search

    @stracks = SentimentHelper::Sentiment.lyrics_keywords(params[:word] + " " + params[:feeling])
    @feeling = params[:feeling]
#    @desired = params[:desired]

    respond_to do |format|
      if @stracks.length > 0
        format.html {render :show, layout: false}
      else
        flash[:danger] = 'There was a problem'
        format.html { render :index }
        format.json { }
      end
    end

  end
end
