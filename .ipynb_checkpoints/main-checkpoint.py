''' MODULES '''
from modules.character_delay_animation import character_delay_animation
from modules.clear_screen import clear_screen
from modules.display_format import display_format
from modules.delay import delay
from modules.display_format import display_format
from modules.display_function import display_function
from modules.display_header import display_header
from modules.display_line import display_line
from modules.error_message import error_message
from modules.insert_spaces import insert_spaces
from modules.line_delay_animation import line_delay_animation
from modules.press_enter_to_continue import press_enter_to_continue

''' IMPORTS '''
import requests, os, keyboard
from dotenv import load_dotenv
import numpy as np
import pandas as pd

load_dotenv() # load .env file

API_KEY= os.getenv('TMDB_API_KEY') # get API key

class Menu:
    ''' ATTRIBUTES '''
    # TMDB API
    URL = "https://api.themoviedb.org/3"

    HEADERS = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    function_list = {
        1: 'view_movies',
        2: 'filter_by_genre',
        3: 'recommend_movie_by_genre',
        4: 'search_movie_by_title',
        5: 'movie_leaderboards',
        6: 'exit'
    }

    ''' METHODS '''
    def authenticate(self):
        response = requests.get(f"{self.URL}/authentication", headers=self.HEADERS)

        if response.status_code == 200:
            print('Authentication successful!')
            print(response.json())

            # redirect to main menu
            self.display_main_menu()
        else:
            print(f"Authentication failed: {response.status_code}")

    def fetch_movies_by_category(self, category, page):
        response = requests.get(
            f"{self.URL}/movie/{category}",
            headers=self.HEADERS,
            params={'page': page}
            )
        
        return response.json() if response.status_code == 200 else None
    
    def fetch_movies_by_genre(self, genre_id, page):
        response = requests.get(
            f"{self.URL}/discover/movie",
            headers=self.HEADERS,
            params={
                'with_genres': genre_id,
                'page': page
            }
        )

        return response.json() if response.status_code == 200 else None

    def fetch_movie_by_title(self, query):
        response = requests.get(
            f"{self.URL}/search/movie",
            headers=self.HEADERS,
            params={'query': query}
        )

        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            return []
        
    def fetch_leaderboards(self):
        popular = requests.get(
            f"{self.URL}/movie/popular",
            headers=self.HEADERS
        )
        top_rated = requests.get(
            f"{self.URL}/movie/top_rated",
            headers=self.HEADERS
        )
        trending_day = requests.get(
            f"{self.URL}/trending/movie/day",
            headers=self.HEADERS
        )
        trending_week = requests.get(
            f"{self.URL}/trending/movie/week",
            headers=self.HEADERS
        )

        popular_movies = popular.json().get('results', [])
        top_rated_movies = top_rated.json().get('results', [])
        trending_day_movies = trending_day.json().get('results', [])
        trending_week_movies = trending_week.json().get('results', [])

        return {
            "Popular": popular_movies,
            "Top Rated": top_rated_movies,
            "Trending Today": trending_day_movies,
            "Trending This Week": trending_week_movies
        }
    
    from requests.exceptions import ReadTimeout

    def fetch_movies(self, endpoint, max_pages=500):
        all_movies = []
        page = 1
        max_retries = 5

        while page <= max_pages:
            url = f'{self.URL}/{endpoint}?page={page}'
            print(f"Fetching {endpoint} | Page {page}")

            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(url, headers=self.HEADERS, timeout=10)  # Timeout added here

                    if response.status_code == 429:
                        print(f"[RATE LIMITED] Waiting 15 seconds before retrying page {page}...")
                        delay(15)
                        continue

                    if response.status_code != 200:
                        print(f"[ERROR] Failed at page {page} of endpoint '{endpoint}'")
                        print(f"Status Code: {response.status_code}")
                        print(f"Response: {response.text}")
                        break

                    data = response.json()
                    all_movies.extend(data.get('results', []))
                    print(f"[INFO] Fetched {len(data.get('results', []))} movies from page {page}")

                    delay(0.5)
                    page += 1
                    break  # Exit retry loop after success

                except ReadTimeout:
                    retries += 1
                    print(f"[TIMEOUT] Read timed out on page {page}. Retrying... ({retries}/{max_retries})")
                    delay(5)

            if retries >= max_retries:
                print(f"[ERROR] Max retries reached on page {page}. Skipping this page.")
                page += 1  # Skip problematic page

        print(f"[DONE] {endpoint}: Total movies fetched = {len(all_movies)}")
        return all_movies

    
    def create_dataset(self):
        # fetch movies
        popular_movies = self.fetch_movies('movie/popular')
        top_rated_movies = self.fetch_movies('movie/top_rated')
        now_playing_movies = self.fetch_movies('movie/now_playing')
        discover_movies = self.fetch_movies('discover/movie')

        # aggregate movies
        all_movies = popular_movies + top_rated_movies + now_playing_movies + discover_movies

        # keep only unique movies
        unique_movies = {movie['id']: movie for movie in all_movies}

        dataset = []

        # make dataset
        for movie in unique_movies.values():
            dataset.append({
                'id': movie.get('id'),
                'title': movie.get('title'),
                'original_title': movie.get('original_title'),
                'overview': movie.get('overview'),
                'release_date': movie.get('release_date'),
                'popularity': movie.get('popularity'),
                'vote_average': movie.get('vote_average'),
                'vote_count': movie.get('vote_count'),
                'genre_ids': movie.get('genre_ids'),
                'original_language': movie.get('original_language')
            })

        # convert to DataFrame
        dataset_df = pd.DataFrame(dataset)

        # convert to .csv file
        dataset_df.to_csv('tmdb_movies_dataset.csv', index=False)

    ''' OPERATIONS '''
    def view_movies(self, category_index=1) -> None:  
        genre_list = { 1: 'popular', 2: 'top_rated', 3: 'upcoming', 4: 'now_playing', 5: 'latest' }
        current_page:int = 1 
        category:str = genre_list[category_index]
        
        while True:
            response = self.fetch_movies_by_category(category, current_page)

            if response is None:
                error_message("Failed to fetch movies", 2)
                return
            
            movies=response.get('results', [])

            # show header
            clear_screen()
            category_display = category.replace('_', ' ').title()
            header_length:int = 19 + len(category_display)
            space_length:int = int(((header_length - len(category) - 6) / 2))

            line_delay_animation(f"[ List of {category_display} Movies ]", 0.01)
            display_format('#', header_length)
            line_delay_animation(f"[^]{' ' * space_length}{category_display}{' ' * space_length}[v]", 0.01)
            display_format('#', header_length)

            # show movies list
            counter:int = 1 + 20 * (current_page - 1)
            for movie in movies[:20]:
                line_delay_animation(f"[{counter}] {movie['title']}", 0.01)
                counter += 1

            # show navigation bar
            navigation_bar:str = f"[<] {' ' if current_page == 1 else current_page - 1}       [{current_page}]       {current_page + 1} [>]"
            display_format('#', len(navigation_bar))
            line_delay_animation(navigation_bar, 0.01)
            display_format('#', len(navigation_bar))

            while True:
                pressed = keyboard.read_key() # listen for key event
                
                # Press [<] - Move one page down
                if pressed == 'left' and current_page > 1:
                    current_page -= 1
                    break
                # Press [>] - Move one page up
                if pressed == 'right':
                    current_page += 1
                    break
                if pressed == 'up':
                    current_page = 1 # reset page
                    if category_index > 1:
                        category_index -= 1
                        category=genre_list[category_index]
                        break
                if pressed == 'down':
                    current_page = 1 # reset page
                    if category_index < 5:
                        category_index += 1
                        category=genre_list[category_index]
                    break
                # Press ESC - Return to main menu
                elif pressed == 'esc':
                    return
                
    def filter_by_genre(self, genre_index=28) -> None:
        current_page:int = 1
        counter:int = 1

        genre_list = {
            28: "Action",
            12: "Adventure",
            16: "Animation",
            35: "Comedy",
            80: "Crime",
            99: "Documentary",
            18: "Drama",
            10751: "Family",
            14: "Fantasy",
            36: "History",
            27: "Horror",
            10402: "Music",
            9648: "Mystery",
            10749: "Romance",
            878: "Science Fiction",
            10770: "TV Movie",
            53: "Thriller",
            10752: "War",
            37: "Western"
        }

        # map genre ids and names
        genre_ids = list(genre_list.keys())
        genre_names = list(genre_list.values())

        while True:
            # display header
            line_delay_animation(f"[ Filter by Genre ]", 0.01)
            display_format('#', 19)

            # display genre list
            for index, name in enumerate(genre_names, start=1):
                line_delay_animation(f"[{index}] {name}", 0.05)

            line_delay_animation(f"[20] << Back", 0.05)

            try:
                genre_choice = int(input(">> ").strip())
                if genre_choice == 20: # return to menu
                    return
                if genre_choice < 1 or genre_choice > len(genre_list):
                    error_message("Invalid input, please enter a valid genre choice", 2)
                
            except ValueError as e:
                error_message(e, 2)
                return

            selected_genre_id = genre_ids[genre_choice - 1]
            selected_genre_name = genre_list[selected_genre_id]
            
            while True:
                response = self.fetch_movies_by_genre(selected_genre_id, current_page)
 
                if response is None:
                    error_message("Failed to fetch movies", 2)
                    return
                
                movies = response.get('results', [])
                    
                # show header
                clear_screen()
                header_length:int = 19 + len(selected_genre_name)
                space_length:int = int(((header_length - len(selected_genre_name) - 6) / 2))

                line_delay_animation(f"[ List of {selected_genre_name} Movies ]", 0.01)
                display_format('#', header_length)

                # show movies list from specified genre
                counter:int = 1 + 20 * (current_page - 1)
                for movie in movies[:20]:
                    line_delay_animation(f"[{counter}] {movie['title']}", 0.01)
                    counter += 1

                # show navigation bar
                navigation_bar:str = f"[<] {' ' if current_page == 1 else current_page - 1}       [{current_page}]       {current_page + 1} [>]"
                display_format('#', len(navigation_bar))
                line_delay_animation(navigation_bar, 0.01)
                display_format('#', len(navigation_bar))

                while True:
                    pressed = keyboard.read_key() # listen for key event
                    
                    # Press [<] - Move one page down
                    if pressed == 'left' and current_page > 1:
                        current_page -= 1
                        break
                    # Press [>] - Move one page up
                    if pressed == 'right':
                        current_page += 1
                        break
                    # Press ESC - Return to main menu
                    if pressed == 'esc':
                        return
                    input()

    def recommend_movie_by_genre(self) -> None:
        print("recommending movie by genre...")
        input()

    def search_movie_by_title(self) -> None:
        while True:
            line_delay_animation('[ Search Movie by Title ]', 0.01)
            display_format('#', 25)
            search_query = input("Search for: ").strip()
            movies = self.fetch_movie_by_title(search_query)

            if movies is None:
                error_message("No movies found.", 2)

            clear_screen()
            line_delay_animation('[ Search Movie by Title ]', 0.01)
            display_format('#', 25) 
            line_delay_animation("#    Search Results:    #", 0.01)
            display_format('#', 25)

            # display top 10 search results
            for idx, movie in enumerate(movies[:10], start=1):  # Limit to first 10 results
                line_delay_animation(f"[{idx}] {movie.get('title', 'N/A')} ({movie.get('release_date', 'N/A')})", 0.1)

            line_delay_animation(f"[11] << Back", 0.05)
            display_format('#', 25)

            while True:
                try:
                    selection = int(input(">> ").strip())

                    if selection == 11: # return to main menu
                        return
                    if selection not in [x for x in range(1, 11)]:
                        error_message("Invalid input, please enter a valid movie choice", 3)

                    else:
                        selected_movie = movies[selection - 1]
                        break

                except ValueError as e:
                    error_message(e, 2)

            # display movie details
            clear_screen()
            line_delay_animation(f"[ {selected_movie.get('title', 'N/A')} ]", 0.01)
            
            print(f"Overview     : {selected_movie.get('overview', 'N/A')}")
            print(f"Release Date : {selected_movie.get('release_date', 'N/A')}")
            print(f"Language     : {selected_movie.get('original_language', 'N/A')}")
            print(f"Popularity   : {selected_movie.get('popularity', 'N/A')}")
            print(f"Vote Average : {selected_movie.get('vote_average', 'N/A')}")
            print(f"Vote Count   : {selected_movie.get('vote_count', 'N/A')}")
            print(f"Genres (IDs)  : {selected_movie.get('genre_ids', [])}")
            
            while True:
                pressed = keyboard.read_key() # listen for key event
                
                # Press ESC - Return to main menu
                if pressed == 'esc':
                    clear_screen()
                    break

    def movie_leaderboards(self) -> None:
        while True:
            leaderboards = self.fetch_leaderboards()

            if leaderboards is None:
                error_message("Failed to fetch movies", 2)
                return
            
            top_3_popular = leaderboards["Popular"][:3]
            top_3_rated = leaderboards["Top Rated"][:3]
            top_3_trending_daily = leaderboards["Trending Today"][:3]
            top_3_trending_weekly = leaderboards["Trending This Week"][:3]

            # show header
            clear_screen()
            header_length:int = 26
            counter:int = 1

            categories = [
                "Popular Movies",
                "Rated Movies",
                "Trending(Daily)",
                "Trending(Weekly)"
            ]

            top_lists = [
                top_3_popular,
                top_3_rated,
                top_3_trending_daily,
                top_3_trending_weekly
            ]

            line_delay_animation(f"{5 * ' '}[ LEADERBOARDS ]", 0.05)
            display_format('#', header_length)

            for category, top_movies in zip(categories, top_lists):
                line_delay_animation(f"[ Top 3 {category} ]", 0.05)
                for idx, movie in enumerate(top_movies, start=1):
                    line_delay_animation(f"[{idx}] {movie.get('title', 'N/A')}", 0.05)
                display_format('#', header_length)

            print("[ESC] Return")

            while True:
                pressed = keyboard.read_key() # listen for key event
                
                # Press ESC - Return to main menu
                if pressed == 'esc':
                    clear_screen()
                    return

            
    def exit(self):
        line_delay_animation("exiting system...", 0.2)
        delay(2)
        exit(0)

    def display_main_menu(self) -> None:
        while True:
            while True:
                clear_screen()
                
                line_delay_animation("`~`~`~ [ BingeMatch ] ~`~`~`", 0.1)
                display_format('#', 28)
                line_delay_animation("[1] | View Movies", 0.1)
                line_delay_animation("[2] | Filter by Genre", 0.1)
                line_delay_animation("[3] | Recommend Movie by Genre", 0.1)
                line_delay_animation("[4] | Search Movie by Title", 0.1)
                line_delay_animation("[5] | Movie Leaderboards", 0.1)
                line_delay_animation("[6] | Exit", 0.1)
                display_format('#', 28)

                try:
                    user_choice = int(input(">> ").strip())
                    
                    if user_choice not in [i for i in range(1, 7)]:
                        error_message("Invalid input, please enter a valid choice", 2)
                    else:
                        clear_screen()
                        break

                except ValueError as e:
                    error_message(f": {e}", 2)

            # invoke function based on mapped function list 
            if hasattr(self, self.function_list[user_choice]):
                method = getattr(self, self.function_list[user_choice])
                method()

    
main = Menu()
# main.authenticate()
main.create_dataset()