Rails.application.routes.draw do
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
  resources :demos, only: [:index, :searchstuff, :show]
  get '/searchstuff', to: 'demos#search'


#Tracks
  root 'tracks#index'
  resources :tracks, only: [:index, :search, :show]
  get "/search", to: "tracks#search"
  get "/search_with_sentiment", to: "tracks#search_with_sentiment"
  get "/search_with_age", to: "tracks#search_with_age"
end
