Rails.application.routes.draw do
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
  root 'tracks#index'
  resources :tracks, only: [:index, :search, :show ]
  get "/search", to: "tracks#search"


  resources :lyrics, only: [:index]

  resources :demos, only: [:index, :searchstuff, :show]
  get '/searchstuff', to: 'demos#search'
end
