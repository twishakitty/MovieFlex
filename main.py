import pandas as pd
from sklearn.cluster import KMeans
from scipy.spatial import distance

def load_data():
    """
    Loads the data from the CSV files and returns the datasets.
    """
    tmdb_df = pd.read_csv("TMDB_movie_dataset_v11.csv")
    # newtmdb_df = pd.read_csv("tmdb_df.csv")
    # newtmdb_df = pd.read_csv("english_movies2.csv")
    # tmdb = "https://drive.google.com/file/d/15Yk5gRIeaElTRyRjNO4NK9dsGQbHf9p1/view?usp=sharing"
    # tmdb = "https://drive.google.com/uc?id=" + tmdb.split('/')[-2]
    # tmdb_df = pd.read_csv(tmdb)
    return tmdb_df

def preprocess_dataframes(tmdb_df):
    """
    Preprocesses the IMDB and Netflix datasets.
    """
    load_data()
    # Drop rows with null values in the 'title' column
    tmdb_df.dropna(subset=['title'], inplace=True)

    # Drop rows with null values in the 'genres' column
    tmdb_df.dropna(subset=['genres'], inplace=True)

    newtmdb_df = tmdb_df.loc[tmdb_df['status'] == 'Released']
    newtmdb_df = newtmdb_df.drop(columns=['vote_average', 'vote_count', 'status', 'revenue', 'runtime', 'adult', 'backdrop_path', 'budget', 'homepage', 'original_title', 'poster_path', 'tagline', 'production_companies', 'production_countries', 'spoken_languages'])

    newtmdb_df['genres'] = newtmdb_df['genres'].str.lower().str.split(', ')
    newtmdb_df['genres'] = newtmdb_df['genres'].apply(lambda x: x if isinstance(x, list) else [])
    
    return newtmdb_df

def select_language(language, tmdb_df):
    if language == 'All':
        newtmdb_df = preprocess_dataframes(tmdb_df)
    if language == 'English':
        newtmdb_df = preprocess_dataframes(tmdb_df)
        newtmdb_df = newtmdb_df[newtmdb_df['original_language'] == 'en']
    if language == 'Filipino':
        newtmdb_df = pd.read_csv("ph_movies.csv")
    if language == 'Korean':
        newtmdb_df = pd.read_csv("korean_movies.csv")
    if language == 'Japanese':
        newtmdb_df = pd.read_csv("japanese_movies.csv")
    return newtmdb_df

def cluster_movies_by_genre(newtmdb_df):
    """
    Cluster movies by genre and add the cluster labels to the dataframe.
    """
    genres_encoded = newtmdb_df['genres'].explode().str.get_dummies().groupby(level=0).sum()
    kmeans = KMeans(n_clusters=10, init='k-means++', random_state=42)
    newtmdb_df['cluster'] = kmeans.fit_predict(genres_encoded)
    return newtmdb_df, genres_encoded

def recommend_movies_nearest_updated_cosine(movie_title, genres_encoded, newtmdb_df, num_recommendations=11):
    """
    Recommends movies based on the provided movie title using cosine similarity.
    """
    if movie_title not in newtmdb_df['title'].values:
        return []

    movie_data = newtmdb_df[newtmdb_df['title'] == movie_title]
    movie_cluster = movie_data['cluster'].iloc[0]
    movie_vector = genres_encoded.loc[movie_data.index].values[0]

    cluster_movies = newtmdb_df[newtmdb_df['cluster'] == movie_cluster]
    cluster_movies_vectors = genres_encoded.loc[cluster_movies.index]

    similarities = cluster_movies_vectors.apply(lambda row: distance.cosine(row, movie_vector), axis=1)
    nearest_movies = similarities.nsmallest(num_recommendations).index

    recommended_movie_titles = newtmdb_df.loc[nearest_movies]['title'].tolist()
    if movie_title in recommended_movie_titles:
        recommended_movie_titles.remove(movie_title)

    return recommended_movie_titles
