import streamlit as st
from main import load_data, preprocess_dataframes, cluster_movies_by_genre, recommend_movies_nearest_updated_cosine, select_language
from tmdbv3api import TMDb, Movie
import random
import os
import sys
from dotenv import load_dotenv

# Initialize the TMDb object with your API key
load_dotenv()

tmdb = TMDb()
tmdb.api_key =  os.getenv("TMDB_API_KEY")
movie_search = Movie()

BASE_TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500/"
DEFAULT_POSTER = "https://via.placeholder.com/500x750.png?text=No+Poster+Available"

genres = ['action', 'science fiction', 'adventure', 'drama', 'crime', 'thriller', 'fantasy', 'comedy', 'romance', 'western', 'mystery', 'war', 'animation', 'family', 'horror', 'music', 'history', 'tv movie', 'documentary']

def main():
    st.markdown(
        """
        <style>
            body {
                background-color: #434343;
                background-image: linear-gradient(315deg, #434343 0%, #000000 74%);
            }
            .css-hby737, .css-17eq0hr {
                background-color: #666;
                color: white;
            }
            input, textarea, button {
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }
            .movie-card {
                background-color: #222;
                border-radius: 10px;
                box-shadow: 2px 2px 10px #000;
                transition: transform 0.2s;
                padding: 10px;
            }
            .movie-card:hover {
                transform: scale(1.05);
            }
            .movie-title {
                color: white;
                font-size: 14px;  
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                max-width: 95%;  
                margin-top: 8px;
                margin-bottom: 4px;
            }
            .movie-info {
                color: silver;
                margin-top: 4px;
            }
            details {
                color: silver;
            }
            details summary {
                cursor: pointer;
                outline: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.title("🎬💪 MovieFlex: Movie Recommendation System")
    st.write("Welcome to MovieFlex!✨ Get started by entering your favorite movie!")

    # Choose a language for the movie results
    language = st.radio(
        "Choose a language for the movie results:",
        ("All", "English", "Filipino", "Korean", "Japanese")
    )

    # Display the selected option
    st.write("You selected:", language)

    auto_trigger = False

    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    if 'potential_matches' not in st.session_state:
        st.session_state.potential_matches = []
    if 'movie_input' not in st.session_state:
        st.session_state.movie_input = ""
    if 'reset_triggered' not in st.session_state:
        st.session_state.reset_triggered = False
    if 'surprise_triggered' not in st.session_state:
        st.session_state.surprise_triggered = False
    if 'language' not in st.session_state:
        st.session_state.language = language
    if 'search_button' not in st.session_state:
        st.session_state.search_button = False

    # If reset was triggered, set the default value of the input widget to an empty string
    default_value = "" if st.session_state.reset_triggered else st.session_state.movie_input

    new_input = st.text_input("🔍 Enter your favorite movie:", value=default_value, key="movie_input")

    tmdb_df = load_data()

    if language != st.session_state.language:
        st.session_state.language = language

    newtmdb_df = select_language(st.session_state.language, tmdb_df)
    st.session_state.dataset = newtmdb_df

    newtmdb_df, genres_encoded = cluster_movies_by_genre(st.session_state.dataset)

    # If there's a change in input, update the session state
    if new_input != st.session_state.movie_input:
        st.session_state.movie_input = new_input
        st.session_state.reset_triggered = False  

    movie_title = st.session_state.movie_input

    if movie_title:
        exact_match = newtmdb_df[newtmdb_df['title'] == movie_title]
        
        if exact_match.empty:  # If exact match doesn't exist, then suggest potential matches
            st.session_state.potential_matches = newtmdb_df[newtmdb_df['title'].str.contains(movie_title, case=False, na=False)]['title'].tolist()
            
            if st.session_state.potential_matches:
                selected_title = st.selectbox("Did you mean one of these?", st.session_state.potential_matches)
                if selected_title:
                    movie_title = selected_title
                    auto_trigger = True  # Setting the flag to trigger automatic recommendations
    col1, col2, col3 = st.columns(3)

    if col1.button('Search', key='btn_get_recommendations', on_click=callback) or auto_trigger or st.session_state.search_button:
        display_chosen_movie(movie_title)
        with st.spinner('Fetching recommendations...'):
            st.session_state.recommendations = recommend_movies_nearest_updated_cosine(
                movie_title, genres_encoded=genres_encoded, newtmdb_df=newtmdb_df
            )
        display_recommendations(st.session_state.recommendations, st.session_state.dataset)

    if col2.button('Generate Random Movie', key='btn_surprise_me'):
        st.session_state.recommendations = []
        st.session_state.potential_matches = []  # Clearing potential matches on reset
        st.session_state.reset_triggered = True 

        movie_title = random.choice(newtmdb_df['title'].tolist())
        with st.spinner('Fetching recommendations...'):
            st.session_state.recommendations = recommend_movies_nearest_updated_cosine(
                movie_title, genres_encoded=genres_encoded, newtmdb_df=newtmdb_df
            )
        display_recommendations(st.session_state.recommendations, st.session_state.dataset)

    if col3.button("Reset", key="btn_reset"):
        st.session_state.recommendations = []
        st.session_state.potential_matches = []  # Clearing potential matches on reset
        st.session_state.reset_triggered = True  # Set the reset flag
        st.session_state.search_button = False
        st.experimental_rerun()

@st.cache_data
def display_chosen_movie(movie_title):
    st.write("You have chosen", movie_title)

    movie_details = fetch_movie_details(movie_title)

    st.markdown(
                f"""
                <div class="movie-card" style="display: flex; align-items: center;">
                    <div style="overflow: hidden; border-radius: 10px; margin-right: 10px;">
                        <img src="{movie_details['poster']}" alt="{movie_title}" style="width: 150px; height: 225px; object-fit: cover;">
                    </div>
                    <div>
                        <a href="https://www.themoviedb.org/tv/{movie_details['id']}" target="_blank">
                            <div class="movie-title">{movie_title}</div>
                        </a>
                        <p class="movie-info">{movie_details['release_date']} | {movie_details['genres']} | Rating: {movie_details['rating']}</p>
                        <details>
                            <summary>Overview</summary>
                            {movie_details['overview']}
                        </details>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

def display_recommendations(recommendations, newtmdb_df):
    st.subheader("Recommended Movies:")

    if 'selected_genres' not in st.session_state:
        st.session_state.selected_genres = []
    
    selected_genres = []

    selected_genres = st.multiselect("Select Genres:", ['All'] + genres, default='All')
    st.session_state.selected_genres = handle_special_options(selected_genres)

    # genreco = get_genres_for_recommendations(recommendations, newtmdb_df)
    # st.write(genreco)
    # st.write(recommendations)
    
    if st.button("Filter movies"):
        st.balloons()
        filter_movies = filter_movies_by_genre(recommendations, st.session_state.selected_genres, newtmdb_df)
        # st.write(recommendations)
        recommendations = filter_movies
        # st.write(filter_movies)

    display_movies(recommendations)

def display_movies(recommendations):
    if recommendations:
        for movie in recommendations:
            movie_details = fetch_movie_details(movie)

            # Display movie details for each row
            st.markdown(
                f"""
                <div class="movie-card" style="display: flex; align-items: center;">
                    <div style="overflow: hidden; border-radius: 10px; margin-right: 10px;">
                        <img src="{movie_details['poster']}" alt="{movie}" style="width: 150px; height: 225px; object-fit: cover;">
                    </div>
                    <div>
                        <a href="https://www.themoviedb.org/movie/{movie_details['id']}" target="_blank">
                            <div class="movie-title">{movie}</div>
                        </a>
                        <p class="movie-info">{movie_details['release_date']} | {movie_details['genres']} | Rating: {movie_details['rating']}</p>
                        <details>
                            <summary>Overview</summary>
                            {movie_details['overview']}
                        </details>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.error("Couldn't find any recommendations for that movie.")

def filter_movies_by_genre(recommendations, selected_genres, newtmdb_df):
    if selected_genres == genres:
        return recommendations
    else:
        filtered_recommendations = []
        for movie_title in recommendations:
            # Find the row in newtmdb_df corresponding to the movie title
            movie_row = newtmdb_df[newtmdb_df['title'] == movie_title]
            if not movie_row.empty:
                # Extract genres for the movie from the DataFrame
                genres_for_movie = movie_row['genres'].values[0]
                # Check if any of the selected genres is in the genres for the movie
                if all(genre in genres_for_movie for genre in selected_genres):
                    filtered_recommendations.append(movie_title)
        return filtered_recommendations

def handle_special_options(selected_genres):
    if 'All' in selected_genres:
        return genres
    else:
        return selected_genres

def callback():
    st.session_state.search_button = True

def get_genres_for_recommendations(recommendations, newtmdb_df):
    genres_for_recommendations = []
    for movie_title in recommendations:
        # Find the row in newtmdb_df corresponding to the movie title
        movie_row = newtmdb_df[newtmdb_df['title'] == movie_title]
        if not movie_row.empty:
            # Extract genres for the movie from the DataFrame
            genres_for_movie = movie_row['genres'].values[0]
            genres_for_recommendations.append(genres_for_movie)
    return genres_for_recommendations

def get_movie_id(movie_title, newtmdb_df):
    # Find the row where the title matches the given movie_title
    movie_row = newtmdb_df[newtmdb_df['title'] == movie_title]
    
    # Check if the movie exists in the DataFrame
    if not movie_row.empty:
        # Extract and return the movie ID
        movie_id = movie_row['id'].values[0]
        return movie_id
    else:
        # Handle the case where the movie title is not found
        return None

def fetch_movie_details(movie_title):
    movie_id = get_movie_id(movie_title, st.session_state.dataset)
    # movie_id = None
    try:
        search_results = movie_search.search(movie_title)
        
        # Check if there are search results
        if not search_results:
            return {
                "id": movie_id,  
                "poster": DEFAULT_POSTER,
                "release_date": "Unknown",
                "rating": "N/A",
                "overview": "No overview available",
                "genres": "Unknown"
            }

        # movie_id = search_results[0].id
        movie_id = get_movie_id(movie_title, st.session_state.dataset)
        movie_details = movie_search.details(movie_id)

        # Extract the required details from the movie details
        return {
            "id": movie_id,  
            "poster": BASE_TMDB_IMAGE_URL + movie_details.poster_path if movie_details.poster_path else DEFAULT_POSTER,
            "release_date": movie_details.release_date if hasattr(movie_details, 'release_date') else "Unknown",
            "rating": str(movie_details.vote_average) if hasattr(movie_details, 'vote_average') else "N/A",
            "overview": movie_details.overview if hasattr(movie_details, 'overview') else "No overview available",
            "genres": ", ".join([genre['name'] for genre in movie_details.genres]) if hasattr(movie_details, 'genres') else "Unknown"
        }

    except Exception as e:
        print(f"An error occurred while fetching details for {movie_title}: {e}")
        return {
            "id": movie_id,  
            "poster": DEFAULT_POSTER,
            "release_date": "Unknown",
            "rating": "N/A",
            "overview": "No overview available",
            "genres": "Unknown"
        }


if __name__ == "__main__":
    main()
