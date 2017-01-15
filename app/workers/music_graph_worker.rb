#
# class MusicGraphWorker
# #  include Sidekiq::Worker
#
#   def perform
#     # @word = "coffee"
#     # url = "http://api.musicgraph.com/api/v2/track/search?api_key=" + ENV['MUSIC_GRAPH_API_KEY'] + "&lyrics_phrase=" + @word
#     # uri = URI(url)
#     # response = Net::HTTP.get(uri)
#     # @tracks = JSON.parse(response)
#
#     view = html = ActionView::Base.new(Rails.root.join('app/views'))
#     view.class.include ApplicationHelper
#     view.render(
#       file: 'tracks/index.html.erb'
#     )
#   end
# end
