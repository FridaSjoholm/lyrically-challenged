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
        format.html { render :_no_results, layout: false }
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

<<<<<<< HEAD
  #Search by what you want to do on what kind of weather day
  def weather_search
    @tracks = TracksHelper::Track.lyrics_keywords(params[:weather], 20).select{ |t| t.match_weather(params[:want_to])}
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
=======

  #Search by age and sentiment
def search_with_age
  @form_feeling = params[:feeling]
  @tracks = TracksHelper::Track.lyrics_keywords(params[:age], 20).select{ |t| t.match_sentiment(@form_feeling)}
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
>>>>>>> 065abc01b688e6d0b3e0de79aa5e1521f66923f1

  def search_for_party
    p "in search_for_party"
    @tracks = TracksHelper::Track.lyrics_keywords(params[:word], 30).select{|t| (t.audio_features.valence > 0.6)==true && (t.audio_features.danceability > 0.6)==true}
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

  def search_for_dance
    p "in search_for_dance"
    @tracks = TracksHelper::Track.lyrics_keywords(params[:word], 30).select{|t| (t.audio_features.tempo > 0.6)==true && (t.audio_features.danceability > 0.6)==true}
    respond_to do |format|
      if @tracks.length > 0
        format.html {render :show, layout: false}
      else
        flash[:danger] = 'There was a problem'
        format.html { render :_no_results, layout: false }
        format.json { }
      end
    end
  end


end
