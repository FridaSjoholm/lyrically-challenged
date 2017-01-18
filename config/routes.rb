Rails.application.routes.draw do
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
  root 'tracks#index'
  resources :tracks, only: [:index, :search, :show, :search_for_party, :search_for_dance]
  get "/search", to: "tracks#search"
  get "/search_with_sentiment", to: "tracks#search_with_sentiment"
  get "/search_for_party", to: "tracks#search_for_party"
  get "/search_for_dance", to: "tracks#search_for_dance"


  resources :demos, only: [:index, :searchstuff, :show]
  get '/searchstuff', to: 'demos#search'

end
