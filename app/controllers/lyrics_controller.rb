class LyricsController < ApplicationController

  def index
    #Sample call to lyricapi
    #http://api.lololyrics.com/0.5/getLyric?artist=Rihanna+J&track=Umbrella

    # https://lyric-api.herokuapp.com/api/find/artist/song

    #set variables
    @song = params[:song]
    @artist = params[:artist]

    #Make call to lololyrics API
    url = "https://lyric-api.herokuapp.com/api/find/#{@artist}/#{@song}"
    uri = URI(url)
  p  @lyrics = Net::HTTP.get(uri)

  end
end
