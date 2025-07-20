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
                    if category_index > 1:
                        category_index -= 1
                        category=genre_list[category_index]
                        break
                if pressed == 'down':
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

            try:
                genre_choice = int(input(">> ").strip())                
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
                    elif pressed == 'esc':
                        return
                    input()

        

    def recommend_movie_by_genre(self) -> None:
        print("recommending movie by genre...")
        input()

    def search_movie_by_title(self) -> None:
        print("searching movie by title...")
        input()

    def movie_leaderboards(self) -> None:
        print("displaying movie leaderboards...")
        input()

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
                    pressed = keyboard.read_key() # listen for key events
                    
                    if pressed not in [str(i) for i in range(1, 7)]:
                        error_message("Invalid input, please enter a valid choice", 2)
                    else:
                        clear_screen()
                        break

                except ValueError as e:
                    error_message(f": {e}", 2)

            # invoke function based on mapped function list 
            if hasattr(self, self.function_list[int(pressed)]):
                method = getattr(self, self.function_list[int(pressed)])
                method()

    
main = Menu()
main.authenticate()