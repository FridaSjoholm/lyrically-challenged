class DemosController < ApplicationController

  def index
    #Sample call to lololyrics
    #http://api.lololyrics.com/0.5/getLyric?artist=Rihanna+J&track=Umbrella

    # http://localhost:3000/demos?song=Umbrella&artist=Rihanna

    #set variables
    @song = params[:song]
    @artist = params[:artist]

    #Make call to lololyrics API
    url = "http://api.lololyrics.com/0.5/getLyric?artist=#{@artist}+J&track=#{@song}"
    uri = URI(url)
    response = Net::HTTP.get(uri)

    #Parse response with Nokogiri
    p noko = Nokogiri::XML.parse(response)
    p @lyrics = noko.children.children.children[1]
  end


#For whitespaces, tried:
# &#160
# %20
# + 


end
