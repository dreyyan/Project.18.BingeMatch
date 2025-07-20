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

    def fetch_movies(self, category, page):
        response = requests.get(
            f"{self.URL}/movie/{category}",
            headers=self.HEADERS,
            params={'page': page}
            )
        
        return response.json() if response.status_code == 200 else None

    def view_movies(self, category='popular') -> None:
        current_page:int = 1
        
        while True:
            response = self.fetch_movies(category, current_page)

            if response is None:
                error_message("Failed to fetch movies", 2)
                return
            
            # show page 1 list of popular movies
            movies=response.get('results', [])

            clear_screen()
            category_display = category.replace('_', ' ').title()
            line_delay_animation(f"[ List of {category_display} Movies ]", 0.01)
            display_format('#', 19 + len(category_display))

            counter:int = 1 + 20 * (current_page - 1)
            for movie in movies[:20]:
                line_delay_animation(f"[{counter}] {movie['title']}", 0.01)
                counter += 1

            navigation_bar:str = f"[<] {current_page - 1}       [{current_page}]       {current_page + 1} [>]"
            display_format('#', len(navigation_bar))
            line_delay_animation(navigation_bar, 0.01)

            while True:
                pressed = keyboard.read_key()

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
                
    def filter_by_genre(self) -> None:
        print("filtering by genre...")
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
                    user_choice = int(input('>> ').strip())
                    
                    if user_choice not in self.function_list.keys():
                        error_message("Invalid input, choice does not exist", 2)
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
main.authenticate()