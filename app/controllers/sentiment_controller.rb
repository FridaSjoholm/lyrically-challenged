class SentimentController < ApplicationController

  include SentimentHelper

  def search

    @stracks = SentimentHelper::Sentiment.lyrics_keywords(params[:word])
    @feeling = params[:feeling]

    if @feeling == "sad"
      p "You want to be sad"
      @sad_tracks = []
      @stracks.each do |track|
        if track.audio_features != nil
          if track.audio_features.valence < 0.4

            @sad_tracks << track
          end
        end
      end
      @feeling_tracks = @sad_tracks
    elsif @feeling == "angry"
      p "You want to be angry"
      @angry_tracks = []
      @stracks.each do |track|
        if track.audio_features != nil
          if track.audio_features.valence >= 0.4 && track.audio_features.valence <= 0.6

            @angry_tracks << track
          end
        end
      end
      @feeling_tracks = @angry_tracks
    elsif @feeling == "calm"
      p "You want to be calm"
      @calm_tracks = []
      @stracks.each do |track|
        if track.audio_features != nil
          if track.audio_features.valence > 0.4 && track.audio_features.tempo < 100

            @calm_tracks << track
          end
        end
      end
      @feeling_tracks = @calm_tracks
    elsif @feeling == "happy"
      p "You want to be happy"
      @happy_tracks = []
      @stracks.each do |track|
        if track.audio_features != nil
          if track.audio_features.valence > 0.6

            @happy_tracks << track
          end
        end
      end
      @feeling_tracks = @happy_tracks

    end
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
