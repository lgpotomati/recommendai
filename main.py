import json
import requests
from flask import Flask, request
from tmdbv3api import TMDb, Movie, TV
from tmdbv3api import Configuration
from googleapiclient.discovery import build

REGION = 'US'

app = Flask(__name__)
tmdb = TMDb()
tmdb.api_key = '79874851eec9bdd87dd5b9cc08c06f73'

@app.route("/")
def input_form():
    html = """
       <!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
	<title>Discover AI-Powered Film Recommendations</title>
	<style>
		body {
			background-color: lightgoldenrodyellow;
			font-size: 16px;
			margin: 0;
			padding: 0;
		}

		h1 {
			color: darkorchid;
			font-size: 48px;
			margin: 0 auto;
			text-align: center;
			padding: 80px 0;
		}

		form {
			background-color: lavender;
			border-radius: 10px;
			box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
			margin: 0 auto;
			max-width: 500px;
			padding: 30px;
		}

		input[type=text] {
			border: none;
			border-radius: 5px;
			box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
			display: block;
			font-size: 14px;
			margin-bottom: 10px;
			padding: 8px;
			width: 100%;
		}

		input[type=submit] {
			background-color: darkorchid;
			border: none;
			border-radius: 5px;
			box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
			color: white;
			cursor: pointer;
			display: block;
			font-size: 16px;
			margin: 20px auto 0;
			padding: 10px 20px;
			transition: background-color 0.2s ease-in-out;
		}

		input[type=submit]:hover {
			background-color: purple;
		}
	</style>
</head>
<body>
	<h1>Discover AI-Powered Film Recommendations</h1>
	<form action="/recommend" method="post">
		1º Favorite Movie: <input type="text" name="a"><br>
		2º Favorite Movie: <input type="text" name="b"><br>
		3º Favorite Movie: <input type="text" name="c"><br>
		<input type="submit" value="Submit">
	</form>
</body>
</html>
"""
    return html


def get_movie_rhyme(favorite_movie1, favorite_movie2, favorite_movie3):
    apikey = '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'
    data = {
        "prompt": f"I love movies, and my favorite movies are {favorite_movie1}, {favorite_movie2}, and {favorite_movie3}. Write a short and dark comic rhyme about my movie taste.",
        "model": "text-davinci-003",
        "temperature": 0.9,
        "max_tokens": 200,
    }
    try:
        response = requests.post("https://api.openai.com/v1/completions", json=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {apikey}",
        })
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return str(e), 500
    response_json = json.loads(response.text)
    try:
        rhyme = response_json["choices"][0]["text"]
    except KeyError as e:
        return f"Error processing response: {str(e)}", 500
    return rhyme.strip()

def get_movie_recommendations(favorite_movie1, favorite_movie2, favorite_movie3):
    apikey = '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'
    data = {
        "prompt": f"I love movies, and my favorite movies are {favorite_movie1}, {favorite_movie2}, and {favorite_movie3}. I want a recommendation of five new movies to watch based on my favorite movies. Please provide the movie names exactly as the following format: movie1;movie2;movie3;movie4;movie5",
        "model": "text-davinci-003",
        "temperature": 0.9,
        "max_tokens": 100,
    }

    try:
        response = requests.post("https://api.openai.com/v1/completions", json=data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {apikey}",
        })
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return str(e), 500

    response_json = json.loads(response.text)

    try:
        recommendation = response_json["choices"][0]["text"]
    except KeyError as e:
        return f"Error processing response: {str(e)}", 500

    return recommendation.strip()
#
api_key = 'AIzaSyCZdJY5-jpck7nQSKbQw7GekEJ-JHuDoqY'
youtube = build('youtube', 'v3', developerKey=api_key)

def get_trailer(movie_name):
    search_response = youtube.search().list(
        q=movie_name + ' trailer',
        part='id,snippet',
        maxResults=1,
        type='video'
    ).execute()

    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            return search_result['id']['videoId']

def get_movie_details(movie_titles):
    movie = Movie()
    tv = TV()
    config = Configuration()

    movie_info = []
    for title in movie_titles:
        result = movie.search(title)
        if not result:
            result = tv.search(title)

        if result:
            item = result[0]
            if 'title' in item:
                details = movie.details(item['id'])
            else:
                details = tv.details(item['id'])

            # Get the movie cover
            config_data = config.info()
            base_url = config_data['images']['secure_base_url']
            file_size = 'w500'
            cover_url = f"{base_url}{file_size}{details['poster_path']}"

            # Get the release year
            release_year = details['release_date'][:4] if 'release_date' in details else details['first_air_date'][:4]

            # Get the synopsis
            synopsis = details['overview']

            # Get the trailer from YouTube API
            trailer_id = get_trailer(title)
            trailer_url = f"https://www.youtube.com/watch?v={trailer_id}"

            # Get the watch providers
            watch_providers = 'None'
            if 'title' in item:
                watch_providers_response = movie.watch_providers(item['id'])
            else:
                watch_providers_response = tv.watch_providers(item['id'])

            if 'results' in watch_providers_response:
                if REGION in watch_providers_response['results']:
                    providers = watch_providers_response['results'][REGION]
                    if 'providers' in providers:
                        provider_names = [p['provider_name'] for p in providers['providers']]
                        watch_providers = ', '.join(provider_names)

            movie_info.append({
                'title': title,
                'cover_url': cover_url,
                'release_year': release_year,
                'synopsis': synopsis,
                'trailer_url': trailer_url,
                'watch_providers': watch_providers
            })

    return movie_info




@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        favorite_movie1 = request.form["a"]
        favorite_movie2 = request.form["b"]
        favorite_movie3 = request.form["c"]
        rhyme = get_movie_rhyme(favorite_movie1, favorite_movie2, favorite_movie3)
        recommendation = get_movie_recommendations(favorite_movie1, favorite_movie2, favorite_movie3)
        # Replace newline characters with line breaks in HTML
        rhyme = rhyme.replace("\n", "<br>")
        recommendation = recommendation.replace("\n", "<br>")
        movie_titles = recommendation.split(';')
        movie_details = get_movie_details(movie_titles)
        # Create movie details HTML
        movies_html = create_movie_details_html(movie_details)

        html = generate_recommendation_page_html(rhyme, movies_html)
        return html
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


def create_movie_details_html(movie_details):
    movies_html = ''
    for movie in movie_details:
        watch_providers_html = f"{REGION}: {movie['watch_providers']}<br>"
        movie_html = f"""
        <div class="movie">
            <h2>{movie['title']} ({movie['release_year']})</h2>
            <img src="{movie['cover_url']}" alt="{movie['title']} cover">
            <p><strong>Synopsis:</strong> {movie['synopsis']}</p>
            <p><strong>Watch Providers:</strong><br>{watch_providers_html}</p>
            <iframe width="560" height="315" src="{movie['trailer_url'].replace('watch?v=', 'embed/')}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
        """
        movies_html += movie_html
    return movies_html


def generate_recommendation_page_html(rhyme, movies_html):
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Your Recommendation</title>
    <style>
        body {{
            background-color: lightgoldenrodyellow;
            font-family: Arial, sans-serif;
            padding: 20px;
        }}
        h1 {{
            color: darkorchid;
            font-size: 48px;
            margin: 0 auto;
            text-align: center;
            padding: 80px 0;
        }}
        p {{
            font-size: 24px;
            line-height: 1.5;
            margin-bottom: 40px;
            text-align: center;
        }}
        .movie {{
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-bottom: 40px;
            padding: 20px;
        }}
        form {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        input[type=submit] {{
            background-color: darkorchid;
            border: none;
            border-radius: 5px;
            box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
            color: white;
            cursor: pointer;
            font-size: 16px;
            margin-top: 40px;
            padding: 10px 20px;
            transition: background-color 0.2s ease-in-out;
        }}
        input[type=submit]:hover {{
            background-color: mediumpurple;
        }}
    </style>
</head>
<body>
    <h1>Your Movie Recommendations</h1>
    <p>{rhyme}</p>
    <div>
        {movies_html}
    </div>
    <form action="/" method="get">
        <input type="submit" value="Try Again">
    </form>
</body>
</html>
    """
    return html


    return html
