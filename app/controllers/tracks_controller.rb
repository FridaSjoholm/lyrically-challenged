class TracksController < ApplicationController

  include TracksHelper

  def index
    #Instead of an array of hashes, maybe there should be a madlib object?
    @questions = [["I want a song that makes me feel ", @sentiments, "emotion"], ["about", @names, "name"]]
  end

#Search just by keyword(s)
  def search
    @tracks = TracksHelper::Track.lyrics_keywords(params[:word])
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

  #Search by keyword and sentiment
  def search_with_sentiment
    @form_feeling = params[:feeling]
    p "in search_with_sentiment"
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

  def feelings_search
    byebug
    @day_feeling = params[:day]
    @tracks = TracksHelper::Track.lyrics_keywords(params[:feeling], 20).select{ |t| t.feelings_day(@day_feeling)}
    respond_to do |format|
      if @track.length > 0
        format.html {render :show, layout: false}
      else
        flash[:danger] = 'There was a problem'
        format.html { render :index }
        format.json { }
      end
    end
  end
end
