class TracksController < ApplicationController

  include TracksHelper
  include SentimentHelper

  def index
    sesntiments = [
      {
        name: "Loved",
        value: 'loved'
      },
      {
        name: "Happy",
        value: 'happy'
      },
      {
        name: "Energetic",
        value: 'energetic'
      },
      {
        name: "Calm",
        value: 'calm'
      },
      {
        name: "Angry",
        value: 'angry'
      },
      {
        name: "Sad",
        value: 'sad'
      }]

      @sentiments = "Loved, Happy, Energetic, Calm, Angry, Sad".split(", ")

      @names = "Jin, Katie, Christian, Frida".split(", ")

    #Instead of an array of hashes, maybe there should be a madlib object?
    @questions = [["I want a song that makes me feel ", @sentiments, "emotion"], ["about", @names, "name"]]
  end

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
end
