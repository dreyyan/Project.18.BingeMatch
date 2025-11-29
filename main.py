""" [IMPORT] Utility Modules """
from modules.clear_screen import clear_screen
from modules.display_format import display_format
from modules.delay import delay
from modules.error_message import error_message
from modules.line_delay_animation import line_delay_animation

""" [IMPORT] Standard Libraries """
import requests, os, keyboard
from dotenv import load_dotenv
import numpy as np
import pandas as pd
import textwrap
from requests.exceptions import ReadTimeout
from datetime import datetime

""" [IMPORT] Machine Learning Libraries """
import ast
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, normalize
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import hstack, csr_matrix

""" [LOAD] Environment Variables """
load_dotenv() # load .env file
API_KEY= os.getenv('TMDB_API_KEY') # get API key

""" Settings """
SYSTEM_TITLE = "BingeMatch"
SYSTEM_VERSION = "v1.0"
SYSTEM_CONSOLE_WIDTH = 50
SYSTEM_DEFAULT_DELAY = 0.05

# [CLASS] Menu System
class Menu:
    """ Attributes """
    # * TMDB API Base URL & Headers
    URL = "https://api.themoviedb.org/3"
    HEADERS = { "accept": "application/json", "Authorization": f"Bearer {API_KEY}" }
    FUNCTION_LIST = {
        0: 'exit',
        1: 'view_movies',
        2: 'filter_by_genre',
        3: 'recommend_movie_by_genre',
        4: 'search_movie_by_title',
        5: 'movie_leaderboards'
    }

    """ Methods: Helpers for TMDB API interactions and Menu System """
    # [METHOD: Helper] Authenticate User
    def authenticate(self):
        response = requests.get(f"{self.URL}/authentication", headers=self.HEADERS)

        if response.status_code == 200:
            print('Authentication successful!')
            print(response.json())

            # redirect to main menu
            self.display_main_menu()
        else:
            print(f"Authentication failed: {response.status_code}")

    # [METHOD: Helper] Fetch Movies from TMDB API
    def fetch_movies_by_category(self, category, page):
        response = requests.get(
            f"{self.URL}/movie/{category}",
            headers=self.HEADERS,
            params={'page': page}
            )
        
        return response.json() if response.status_code == 200 else None
    
    # [METHOD: Helper] Fetch Movies by Genre from TMDB API
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

    # [METHOD: Helper] Fetch Movie by Title from TMDB API
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
        
    # [METHOD: Helper] Fetch Leaderboards from TMDB API
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

    # [METHOD: Helper] Fetch Movies (with error handling and retries)
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

                except requests.ReadTimeout:
                    retries += 1
                    print(f"[TIMEOUT] Read timed out on page {page}. Retrying... ({retries}/{max_retries})")
                    delay(5)

            if retries >= max_retries:
                print(f"[ERROR] Max retries reached on page {page}. Skipping this page.")
                page += 1  # Skip problematic page

        print(f"[DONE] {endpoint}: Total movies fetched = {len(all_movies)}")
        return all_movies

    # [METHOD: Helper] Create Dataset from TMDB API
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

    # [METHOD: Helper] Print Centered Text
    def print_center(self, text: str, width: int) -> None:
        if len(text) >= width:
            print(text)
            return
        
        padding = (width - len(text)) // 2
        print(" " * padding + text)

    # [METHOD: Helper] Print Centered Text with Fill Symbol 
    def print_center_filled(self, text: str, symbol: str, width: int) -> None:
        if len(text) >= width:
            print(text)
            return
        
        padding = (width - len(text)) // 2
        print(symbol * padding + text + symbol * padding)

    # [METHOD: Helper] Truncate Movie Title
    def truncate_movie_title(self, title: str, offset: int) -> str:
        if len(title) + offset <= SYSTEM_CONSOLE_WIDTH:
            return title
        return title[:SYSTEM_CONSOLE_WIDTH - offset] + "..."
    
    """ Methods: UI """
    # [METHOD: UI] Display System Header
    def display_header(self, ms_delay: float) -> None:
        line_delay_animation(f"`~`~`~`~`~`~`~`~` [ {SYSTEM_TITLE} ] `~`~`~`~`~`~`~`~`", ms_delay)

    # [METHOD: UI] Display System Version
    def display_version(self, ms_delay: float) -> None:
        line_delay_animation(F"###################### {SYSTEM_VERSION} ######################", ms_delay)

    """ Methods: Menu System Functionalities """
    # [METHOD] View Movies by Category
    def view_movies(self, category_index=1) -> None:  
        genre_list = { 1: 'popular', 2: 'top_rated', 3: 'upcoming', 4: 'now_playing', 5: 'latest' }
        current_page:int = 1 
        category:str = genre_list[category_index]
        
        # This loop handles category and page navigation
        while True:
            # fetch movies for the current category and page
            response = self.fetch_movies_by_category(category, current_page)

            # ! [ERROR] Failed to fetch movies
            if response is None:
                error_message("Failed to fetch movies", 2)
                return
            
            # get movies list
            movies=response.get('results', [])

            category_display = category.replace('_', ' ').title()
            space_length:int = int(((SYSTEM_CONSOLE_WIDTH - len(category) - 6) / 2))

            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(f" List of {category_display} Movies ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            # show category with arrows
            print(f"[^]{' ' * space_length}{category_display}{' ' * space_length}[v]")
            display_format('=', SYSTEM_CONSOLE_WIDTH)

            # show movies list
            counter:int = 1 + 10 * (current_page - 1)
            for movie in movies[:10]:
                if counter < 10:
                    print(f"  ", end="")
                else: print(f" ", end="")
                line_delay_animation(f"[{counter}] {self.truncate_movie_title(movie['title'], 9)}", SYSTEM_DEFAULT_DELAY)
                counter += 1
            line_delay_animation("[ESC] Return", SYSTEM_DEFAULT_DELAY)

            # show navigation bar
            navigation_bar:str = f"[<] {' ' if current_page == 1 else current_page - 1}                  [{current_page}]                  {current_page + 1} [>]"
            display_format('#', SYSTEM_CONSOLE_WIDTH)
            print(navigation_bar)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

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
                # Press [^] - Move one category down
                if pressed == 'up':
                    current_page = 1 # reset page
                    if category_index > 1:
                        category_index -= 1
                        category=genre_list[category_index]
                        break
                # Press [V] - Move one category up
                if pressed == 'down':
                    current_page = 1 # reset page
                    if category_index < 5:
                        category_index += 1
                        category=genre_list[category_index]
                    break
                # Press [ESC] - Return to main menu
                elif pressed == 'esc':
                    return
                
    # [METHOD] Filter Movies by Genre
    def filter_by_genre(self) -> None:
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

        genre_ids   = list(genre_list.keys())
        genre_names = list(genre_list.values())

        GENRES_PER_PAGE = 10
        total_pages = 2
        genre_page = 1

        while True:
            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(" Filter by Genre ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            start = (genre_page - 1) * GENRES_PER_PAGE
            end   = start + GENRES_PER_PAGE

            page_genres = list(enumerate(
                genre_names[start:end],
                start=start + 1
            ))

            # show genres list
            for idx, name in page_genres:
                if idx < 10: print("  ", end="")
                else: print(" ", end="")
                line_delay_animation(f"[{idx}] {name}", SYSTEM_DEFAULT_DELAY)
            print("[ESC] Return")


            # show navigation bar
            navigation_bar = f"[<] {' ' if genre_page == 1 else genre_page - 1}                  [{genre_page}]                  {' ' if genre_page == total_pages else genre_page + 1} [>]"
            display_format('#', SYSTEM_CONSOLE_WIDTH)
            print(navigation_bar)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            pressed = keyboard.read_key() # listen for key event

            # Press [<] - Move one page down
            if pressed == "left" and genre_page > 1:
                genre_page -= 1
                continue

            # Press [>] - Move one page up
            if pressed == "right" and genre_page < total_pages:
                genre_page += 1
                continue

            # Press [ESC] - Return to main menu
            if pressed == "esc":
                return

            # Genre selection
            if pressed.isdigit(): # type: ignore
                genre_idx = int(pressed)

                # ! [ERROR] Invalid genre selection
                if genre_idx < 1 or genre_idx > len(page_genres):
                    error_message("Invalid genre selection", 2)
                    continue

                actual_index = start + genre_idx - 1
                selected_genre_id   = genre_ids[actual_index]
                selected_genre_name = genre_names[actual_index]

            else: continue

            # Display movies of selected genre
            current_page = 1

            # This loop handles paging within the selected genre
            while True:
                # display UI
                clear_screen()
                self.display_header(0.1)
                self.display_version(0.1)

                # fetch movies for the selected genre and page
                response = self.fetch_movies_by_genre(selected_genre_id, current_page)

                # ! [ERROR] Failed to fetch movies
                if response is None:
                    error_message("Failed to fetch movies", 2)
                    return

                # get movies list
                movies = response.get('results', [])

                self.print_center_filled(f" List of {selected_genre_name} Movies ", '=', SYSTEM_CONSOLE_WIDTH)
                display_format('#', SYSTEM_CONSOLE_WIDTH)

                counter = 1 + 10 * (current_page - 1)

                for movie in movies[:10]:
                    if counter < 10:
                        print(f"  ", end="")
                    else: print(f" ", end="")
                    line_delay_animation(f"[{counter}] {self.truncate_movie_title(movie['title'], 9)}", SYSTEM_DEFAULT_DELAY)
                    counter += 1
                print("[ESC] Return")

                # show navigation bar
                navigation_bar = f"[<] {' ' if current_page == 1 else current_page - 1}                  [{current_page}]                  {current_page + 1} [>]"
                display_format('#', SYSTEM_CONSOLE_WIDTH)
                print(navigation_bar)
                display_format('#', SYSTEM_CONSOLE_WIDTH)

                while True:
                    pressed = keyboard.read_key()

                    # Same paging behavior as view_movies
                    if pressed == 'left' and current_page > 1:
                        current_page -= 1
                        break

                    if pressed == 'right':
                        current_page += 1
                        break

                    if pressed == 'esc':
                        break

    # [METHOD] Recommend Movie by Genre
    def recommend_movie_by_genre(self) -> None:
        # display UI
        clear_screen()
        self.display_header(0.1)
        self.display_version(0.1)
        self.print_center_filled(f" Movie Recommender ", '=', SYSTEM_CONSOLE_WIDTH)
        display_format('#', SYSTEM_CONSOLE_WIDTH)

        # Load your REAL model only once
        if not hasattr(self, 'recommender_ready'):
            print("[INFO] Loading movie recommendation model...")
            delay(2)

            df = pd.read_csv('tmdb_movies_dataset.csv')
            df['title'] = df['title'].fillna("Unknown Movie")
            df['overview'] = df['overview'].fillna("")
            df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
            df['release_year'] = df['release_date'].dt.year.fillna(2025).astype(int)

            # Fix genre_ids properly
            def parse_genres(x):
                if pd.isna(x): return []
                try: return ast.literal_eval(x)
                except: return []
            df['genre_ids'] = df['genre_ids'].apply(parse_genres)

            # Your exact feature engineering
            tfidf = TfidfVectorizer(stop_words='english', max_features=10000)
            overview_tfidf = tfidf.fit_transform(df['overview'])
            mlb = MultiLabelBinarizer()
            genre_features = mlb.fit_transform(df['genre_ids'])
            num = df[['popularity', 'vote_average', 'vote_count']].fillna(0)
            scaler = StandardScaler()
            num_scaled = scaler.fit_transform(num)

            X = hstack([
                overview_tfidf * 2.0,
                csr_matrix(genre_features) * 1.5,
                csr_matrix(num_scaled),
                csr_matrix(df[['release_year']].values)
            ], format='csr')

            # Best model: brute-force cosine
            nn = NearestNeighbors(n_neighbors=11, metric='cosine', algorithm='brute', n_jobs=-1)
            nn.fit(X)

            self.df = df
            self.X = X
            self.nn = nn
            self.recommender_ready = True
            print("AI engine ready — type any movie!")

        while True:
            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(f" Movie Recommender ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            # prompt user to enter a movie title to search
            query = input("Seaarch for a movie: ").strip()
            if query.lower() in ['back', 'exit', 'quit', '']:
                return

            # Search for matches (fuzzy + case insensitive)
            matches = self.df[
                self.df['title'].str.contains(query, case=False, na=False)
            ].copy()

            # ! [ERROR]: No movies found
            if matches.empty:
                error_message("No movies found with that name. Try again!", 2)
                continue

            # Sort by popularity + rating
            matches = matches.sort_values(['vote_average', 'popularity'], ascending=False).head(10)
            matches = matches.reset_index(drop=True)

            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(f" Found {len(matches)} match(es) for \"{query}\": ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            for i, row in matches.iterrows():
                year = row['release_year'] if row['release_year'] < 2025 else "?"
                # prepare the left part: "[1] Movie Title (2025)"
                left_part = f"[{i+1}] {self.truncate_movie_title(row['title'], 22)} ({year})"
                # prepare the right part: "★ 8.7"
                right_part = f"★ {row['vote_average']:.1f}"
                
                # calculate remaining spaces
                space_count = SYSTEM_CONSOLE_WIDTH - len(left_part) - len(right_part)
                spaces = " " * max(space_count, 1)  # at least one space

                # final line
                movie_line = f"{left_part}{spaces}{right_part}"
                line_delay_animation(movie_line, SYSTEM_DEFAULT_DELAY)
    
            print(f"[{len(matches)+1}] Search again")
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            try:
                choice = int(input("Choose a movie: ").strip())
                if choice == len(matches) + 1:
                    continue
                if not 1 <= choice <= len(matches):
                    raise ValueError
            except:
                error_message("\nInvalid choice", 2)
                continue

            selected_row = matches.iloc[choice - 1]
            selected_idx = selected_row.name  # actual index in full df

            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(f" Movie Recommender ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)
            movie = f"\"{selected_row['title']} ({selected_row['release_year']})\" ★ {selected_row['vote_average']:.1f}"
            self.print_center(f"You like: {self.truncate_movie_title(movie, 13)}", SYSTEM_CONSOLE_WIDTH)
            self.print_center("AI recommends these 10 movies for your next watch:", SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            distances, indices = self.nn.kneighbors(self.X[selected_idx], n_neighbors=11)

            # display AI recommended movies
            for i, idx in enumerate(indices[0][1:], 1):
                m = self.df.iloc[idx]
                year = m['release_year'] if m['release_year'] < 2025 else "?"
                sim = 1 - distances[0][i]
                
                # Properly truncate the recommended movie title
                rec_title = self.truncate_movie_title(f"{i:2}. {m['title']}", 7)
                
                line_delay_animation(f"{rec_title} ({year})", SYSTEM_DEFAULT_DELAY)
                line_delay_animation(f"    Rating: ★ {m['vote_average']:.1f} | Similarity: {sim:.3f}", SYSTEM_DEFAULT_DELAY)
                display_format('=', SYSTEM_CONSOLE_WIDTH)

            display_format('#', SYSTEM_CONSOLE_WIDTH)
            print("[ESC] Return")

            while True:
                pressed = keyboard.read_key()
                if pressed == 'esc':
                    break

    # [METHOD] Search Movie by Title
    def search_movie_by_title(self) -> None:
        while True:
            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(f" Search Movie by Title ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            # prompt user to enter movie title to search
            search_query = input("Search for a movie: ").strip()
            movies = self.fetch_movie_by_title(search_query)

            if movies is None:
                error_message("No movies found.", 2)

            # display results
            while True:
                clear_screen()
                self.display_header(0.1)
                self.display_version(0.1)
                self.print_center_filled(" Search Results ", '=', SYSTEM_CONSOLE_WIDTH)
                display_format('#', SYSTEM_CONSOLE_WIDTH)

                # show top 10 results
                for idx, movie in enumerate(movies[:10], start=1):
                    if idx < 10:
                        print("  ", end="")
                    else:
                        print(" ", end="")

                    title = movie.get('title', 'N/A')
                    date = movie.get('release_date', 'N/A')
                    line_delay_animation(
                        f"[{idx}] {self.truncate_movie_title(title)} ({date})",
                        SYSTEM_DEFAULT_DELAY,
                    )

                print("[ESC] Return")

                display_format('#', SYSTEM_CONSOLE_WIDTH)

                # ----- KEY INPUT -----
                pressed: str = keyboard.read_key()

                # EXIT search
                if pressed == "esc":
                    return

                # MOVIE SELECTION
                if pressed.isdigit():   # type: ignore
                    selection = int(pressed)

                    if selection < 1 or selection > len(movies[:10]):
                        error_message("Invalid movie selection", 2)
                        continue

                    selected_movie = movies[selection - 1]
                else:
                    continue

                # ----- MOVIE DETAILS VIEW -----
                while True:
                    clear_screen()
                    self.display_header(0.1)
                    self.display_version(0.1)
                    self.print_center_filled(
                        f" {selected_movie.get('title','N/A')} ",
                        '=',
                        SYSTEM_CONSOLE_WIDTH,
                    )
                    display_format('#', SYSTEM_CONSOLE_WIDTH)

                    # wrap overview content
                    overview = selected_movie.get('overview', 'N/A')
                    wrapped_overview = textwrap.fill(
                        overview,
                        width=50,
                        initial_indent="    Overview : ",
                        subsequent_indent="               "
                    )

                    # format date
                    release_date_str = selected_movie.get('release_date', 'N/A')
                    if release_date_str != 'N/A':
                        try:
                            dt = datetime.strptime(release_date_str, "%Y-%m-%d")
                            formatted_date = dt.strftime("%b %d, %Y")
                        except ValueError:
                            formatted_date = release_date_str
                    else: formatted_date = release_date_str

                    # format language
                    language_code = selected_movie.get('original_language', 'N/A')
                    language_map = {
                        "en": "English (EN)",
                        "fr": "French (FR)",
                        "es": "Spanish (ES)",
                        "ja": "Japanese (JA)",
                        "ko": "Korean (KO)"
                    }
                    formatted_language = language_map.get(language_code, language_code)

                    # display movie information
                    print(wrapped_overview)
                    print(f"Release Date : {formatted_date}")
                    print(f"    Language : {formatted_language}")
                    print(f"  Popularity : {selected_movie.get('popularity', 'N/A')}")
                    print(f"Vote Average : {selected_movie.get('vote_average', 'N/A')}")
                    print(f"  Vote Count : {selected_movie.get('vote_count', 'N/A')}")
                    print(f"Genres (IDs) : {selected_movie.get('genre_ids', [])}")
                    display_format('#', SYSTEM_CONSOLE_WIDTH)
                    print("[ESC] Back")

                    pressed = keyboard.read_key()

                    # return to search results
                    if pressed == "esc":
                        break

    # [METHOD] Movie Leaderboards
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

            # display UI
            clear_screen()
            self.display_header(0.1)
            self.display_version(0.1)
            self.print_center_filled(f" Leaderboards ", '=', SYSTEM_CONSOLE_WIDTH)
            display_format('#', SYSTEM_CONSOLE_WIDTH)

            # display top 3 per category
            for category, top_movies in zip(categories, top_lists):
                self.print_center_filled(f" Top 3 {category} ", '=', SYSTEM_CONSOLE_WIDTH)
                for idx, movie in enumerate(top_movies, start=1):
                    line_delay_animation(f"{idx}. {movie.get('title', 'N/A')}", SYSTEM_DEFAULT_DELAY)
            display_format('=', SYSTEM_CONSOLE_WIDTH)
            print("[ESC] Return")

            while True:
                pressed = keyboard.read_key() # listen for key event
                
                # Press [ESC] - Return to main menu
                if pressed == 'esc':
                    clear_screen()
                    return


    # [METHOD] Exit System      
    def exit(self):
        exit(0)

    # [METHOD] Display Main Menu
    def display_main_menu(self) -> None:
        while True:
            while True:
                clear_screen()
                
                self.display_header(0.1)
                self.display_version(0.1)
                display_format('=', 50)
                line_delay_animation("[0] | Exit", 0.1)
                line_delay_animation("[1] | View Movies", 0.1)
                line_delay_animation("[2] | Filter by Genre", 0.1)
                line_delay_animation("[3] | Recommend Movie by Genre", 0.1)
                line_delay_animation("[4] | Search Movie by Title", 0.1)
                line_delay_animation("[5] | Movie Leaderboards", 0.1)
                display_format('=', 50)

                try:
                    user_choice = int(input(">> ").strip())
                    
                    if user_choice not in [i for i in range(0, 6)]:
                        error_message("Invalid input, please enter a valid choice", 2)
                    else:
                        clear_screen()
                        break

                except ValueError as e:
                    error_message(f": {e}", 2)

            # invoke function based on mapped function list 
            if hasattr(self, self.FUNCTION_LIST[user_choice]):
                method = getattr(self, self.FUNCTION_LIST[user_choice])
                method()

# [MAIN] Program Entry Point
if __name__ == "__main__":
    main = Menu()
    main.authenticate()
    # main.create_dataset() # uncomment to create dataset from TMDB API