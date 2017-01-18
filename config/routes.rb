Rails.application.routes.draw do
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
  root 'tracks#index'
  resources :tracks, only: [:index, :search, :show]
  get "/search", to: "tracks#search"
  get "/search_with_sentiment", to: "tracks#search_with_sentiment"

  resources :demos, only: [:index, :searchstuff, :show]
  get '/searchstuff', to: 'demos#search'


  get "/feelings_search", to: "tracks#feelings_search"
end
