""" [IMPORT] Modules """
from modules.character_delay_animation import character_delay_animation
from modules.clear_screen import clear_screen
from modules.display_format import display_format
from modules.delay import delay
from modules.display_function import display_function
from modules.display_header import display_header
from modules.display_line import display_line
from modules.error_message import error_message
from modules.insert_spaces import insert_spaces
from modules.line_delay_animation import line_delay_animation
from modules.press_enter_to_continue import press_enter_to_continue

''' [IMPORT] Standard Libraries '''
import requests, os, keyboard
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from requests.exceptions import ReadTimeout

load_dotenv() # load .env file

API_KEY= os.getenv('TMDB_API_KEY') # get API key

""" [CLASS] Menu """
class Menu:
    """ Attributes """
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

    """ METHODS """
    # [METHOD] Authenticate User
    def authenticate(self):
        response = requests.get(f"{self.URL}/authentication", headers=self.HEADERS)

        if response.status_code == 200:
            print('Authentication successful!')
            print(response.json())

            # redirect to main menu
            self.display_main_menu()
        else:
            print(f"Authentication failed: {response.status_code}")

    # [METHOD] Fetch Movies from TMDB API
    def fetch_movies_by_category(self, category, page):
        response = requests.get(
            f"{self.URL}/movie/{category}",
            headers=self.HEADERS,
            params={'page': page}
            )
        
        return response.json() if response.status_code == 200 else None
    
    # [METHOD] Fetch Movies by Genre from TMDB API
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

    # [METHOD] Fetch Movie by Title from TMDB API
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
        
    # [METHOD] Fetch Leaderboards from TMDB API
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

    # [METHOD] Fetch Movies (with error handling and retries)
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

    # [METHOD] Create Dataset from TMDB API
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

    # [METHOD] View Movies by Category
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

            print(f"[ List of {category_display} Movies ]")
            display_format('#', header_length)
            print(f"[^]{' ' * space_length}{category_display}{' ' * space_length}[v]")
            display_format('#', header_length)

            # show movies list
            counter:int = 1 + 20 * (current_page - 1)
            for movie in movies[:20]:
                print(f"[{counter}] {movie['title']}", )
                counter += 1

            print("(ESC) Return")

            # show navigation bar
            navigation_bar:str = f"[<] {' ' if current_page == 1 else current_page - 1}       [{current_page}]       {current_page + 1} [>]"
            display_format('#', len(navigation_bar))
            print(navigation_bar)
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
                
    # [METHOD] Filter Movies by Genre
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
            print(f"[ Filter by Genre ]")
            display_format('#', 19)

            # display genre list
            for index, name in enumerate(genre_names, start=1):
                print(f"[{index}] {name}")

            print(f"[20] Back")

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

                print(f"[ List of {selected_genre_name} Movies ]")
                display_format('#', header_length)

                # show movies list from specified genre
                counter:int = 1 + 20 * (current_page - 1)
                for movie in movies[:20]:
                    print(f"[{counter}] {movie['title']}")
                    counter += 1

                print(f"(ESC) Return")

                # show navigation bar
                navigation_bar:str = f"[<] {' ' if current_page == 1 else current_page - 1}       [{current_page}]       {current_page + 1} [>]"
                display_format('#', len(navigation_bar))
                print(navigation_bar)
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

    # [METHOD] Recommend Movie by Genre
    # [METHOD] Search any movie you love → Get 10 PERFECT AI recommendations
    def recommend_movie_by_genre(self) -> None:
        clear_screen()
        print(" SEARCH A MOVIE YOU LOVE — AI RECOMMENDS 10 MORE ".center(80, '='))
        print()

        # Load your REAL model only once
        if not hasattr(self, 'recommender_ready'):
            print("Loading your movie recommendation engine... (15-20s first time)")
            delay(2)

            import ast
            import pandas as pd
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.preprocessing import MultiLabelBinarizer, StandardScaler, normalize
            from sklearn.decomposition import TruncatedSVD
            from sklearn.neighbors import NearestNeighbors
            from scipy.sparse import hstack, csr_matrix

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
            clear_screen()
            print(" SEARCH A MOVIE YOU LOVE ".center(80, '='))
            print()
            query = input("Enter movie title (or 'back' to return): ").strip()
            if query.lower() in ['back', 'exit', 'quit', '']:
                return

            # Search for matches (fuzzy + case insensitive)
            matches = self.df[
                self.df['title'].str.contains(query, case=False, na=False)
            ].copy()

            if matches.empty:
                error_message("No movies found with that name. Try again!", 2)
                delay(2)
                continue

            # Sort by popularity + rating
            matches = matches.sort_values(['vote_average', 'popularity'], ascending=False).head(10)
            matches = matches.reset_index(drop=True)

            clear_screen()
            print(f" Found {len(matches)} match(es) for \"{query}\":")
            display_line('#', 40)
            for i, row in matches.iterrows():
                year = row['release_year'] if row['release_year'] < 2025 else "?"
                print(f"[{i+1}] {row['title']} ({year})  ★ {row['vote_average']:.1f}")
            print(f"[{len(matches)+1}] Search again")
            display_line('#', 40)

            try:
                choice = int(input(">> Choose a movie (number): ").strip())
                if choice == len(matches) + 1:
                    continue
                if not 1 <= choice <= len(matches):
                    raise ValueError
            except:
                error_message("Invalid choice!", 2)
                delay(2)
                continue

            selected_row = matches.iloc[choice - 1]
            selected_title = selected_row['title']
            selected_idx = selected_row.name  # actual index in full df

            clear_screen()
            print(f" YOU LOVE: {selected_title} ({selected_row['release_year']}) ★ {selected_row['vote_average']:.1f}".center(80))
            print()
            print(" HERE ARE 10 MOVIES THE AI KNOWS YOU'LL LOVE:".center(80))
            print()
            display_line('#', 80)

            # REAL RECOMMENDATION USING YOUR MODEL
            distances, indices = self.nn.kneighbors(self.X[selected_idx], n_neighbors=11)

            for i, idx in enumerate(indices[0][1:], 1):
                m = self.df.iloc[idx]
                year = m['release_year'] if m['release_year'] < 2025 else "?"
                sim = 1 - distances[0][i]
                print(f"{i:2}. {m['title']} ({year})")
                print(f"     Rating: {m['vote_average']:.1f} | Similarity: {sim:.3f}\n")

            display_line('#', 80)
            print("Powered by YOUR DSA Final Project — Real Content-Based AI".center(80))
            print()
            press_enter_to_continue()
            break  # go back to main menu after one recommendation

    # [METHOD] Search Movie by Title
    def search_movie_by_title(self) -> None:
        while True:
            print('[ Search Movie by Title ]')
            display_format('#', 25)
            search_query = input("Search for: ").strip()
            movies = self.fetch_movie_by_title(search_query)

            if movies is None:
                error_message("No movies found.", 2)

            clear_screen()
            print('[ Search Movie by Title ]')
            display_format('#', 25) 
            print("#    Search Results:    #")
            display_format('#', 25)

            # display top 10 search results
            for idx, movie in enumerate(movies[:10], start=1):  # Limit to first 10 results
                print(f"[{idx}] {movie.get('title', 'N/A')} ({movie.get('release_date', 'N/A')})")

            print(f"[11] << Back")
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
            print(f"[ {selected_movie.get('title', 'N/A')} ]")
            
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

            print(f"{5 * ' '}[ LEADERBOARDS ]")
            display_format('#', header_length)

            for category, top_movies in zip(categories, top_lists):
                print(f"[ Top 3 {category} ]")
                for idx, movie in enumerate(top_movies, start=1):
                    print(f"[{idx}] {movie.get('title', 'N/A')}")
                display_format('#', header_length)

            print("(ESC) Return")

            while True:
                pressed = keyboard.read_key() # listen for key event
                
                # Press ESC - Return to main menu
                if pressed == 'esc':
                    clear_screen()
                    return


    # [METHOD] Exit System      
    def exit(self):
        line_delay_animation("exiting system...", 0.2)
        delay(2)
        exit(0)

    # [METHOD] Display Main Menu
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

# [MAIN] Program Entry Point
if __name__ == "__main__":
    main = Menu()
    main.authenticate()
    # main.create_dataset() # uncomment to create dataset from TMDB API