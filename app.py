from openai import OpenAI
from flask import Flask, jsonify, render_template, url_for,redirect, request
import os
from dotenv import load_dotenv
import requests
import json

#for our MovieFormatter Object
from pydantic import BaseModel 
from typing import Optional, List

#request vs requests:
#request from Flask is for incoming HTTP requests to my flask server
#requests from python lib is for sending HTTP requests to other API's or Servers

#app object resprents our web app, instance of flask class
app = Flask(__name__)


#this route decorator connects this url to homeFunc()
#whatever is returned is what the visitor sees in their browser
@app.route('/') #string inside is the URL path: https://localhost:5000/
def root():
    """
    redirects from root to homepage

    returns: redirect to homePage
    """
    return redirect(url_for('homePage'))
    #return "welcome to the home page of this movie proj"
    
@app.route('/home')
def homePage():
    """
    renders the index.html file

    returns: the home page
    """
    return render_template("index.html")
    #datas = currentPopularMovies()['results']
    #return render_template("index.html",datas=datas)

#endpoint for js to fetch to get the top trending movies
#returns first page of current trending movies
@app.route('/popularMovies')
def currentPopularMovies():
    url = "https://api.themoviedb.org/3/movie/popular"
    headers = {
        "accept":"application/json"
    }
    params={
        "language" : "en-US",
        "api_key": os.getenv("TMDB_API_KEY"),  #api key
        "page" : 1
    }
    response = requests.get(url,headers=headers,params=params)

    #error with the fetching the movies
    if response.status_code != 200:
        print("error:", response.status_code) 
        return response.status_code
    else:#good to continue
        data=response.json()
        return jsonify(data)


#POST request is HTTP method when client sends data to the server
@app.route('/MovieRecForUserPrompt', methods=['POST'])
def MovieRecommendationForUserEndPoint():
    #parses incoming json from the client
    userPrompt = request.get_json().get('userPrompt')
    print(userPrompt)
    print(aifunc(userPrompt))
    return jsonify(userPrompt) 


def aifunc(userPrompt):
    #load env variables from the .env file
    load_dotenv()

    #get my API key for OPENAI
    api_key = os.getenv("OPENAI_API_KEY")
    #check if the api_key is empty or missing
    if not api_key:
        raise ValueError("OPENAI key was not found")
        #raise a ValueError if true
    
    #initilize openAI object
    client = OpenAI(api_key=api_key)

    #creating/sending prompt
    response = client.responses.parse(
        model = "gpt-4o",
        input = [
            {"role" : "system", "content": "You're a movie search assistant. Your job is to convert the user's natural language movie request "
            "into a structured JSON object that matches the MovieFormatter BaseModel for the TMDB Discover Get Method. "
            "AND/OR Logic: comma's (,) are treated like an AND query while pipe's (|) are treated like an OR. "
            "If the user refers to actors or actresses (people seen in the movie), always use 'with_cast' even if 'AND' or 'OR' is used"
            "Only use 'with_people' if the user mentions a writer, director, crew, or when the role is not seen in the actual movie"
            "(don't convert person ID, just use their names): "
            "certification, certification.gte, certification.lte, certification_country, "
            "include_adult, include_video, primary_release_year, primary_release_date.gte, primary_release_date.lte, region,"
            "release_date.gte, release_date.lte, vote_average.gte, vote_average.lte, vote_count.gte, vote_count.lte, watch_region, with_cast, with_companies,"
            "with_crew, with_genres, with_keywords, with_origin_country, with_original_language, with_people, with_release_type, with_runtime.gte,"
            " with_runtime.lte, with_watch_monetization_types, with_watch_providers, without_companies, without_genres, without_keywords,"
            "without_watch_providers, year. "
            "Format your response strictly as a JSON object that fits the MovieFormatter BaseModel, do include extra text or explanation"},
            
            {"role": "user", "content": userPrompt}
        ],
        text_format = MovieFormatter #where my pydantic baseModel is used
    )
    return response.output_parsed

#optional means its okay if the user does not give a value for this specific attribute
class MovieFormatter(BaseModel):
    certification: Optional[str] = None
    certification_gte: Optional[str] = None
    certification_lte: Optional[str] = None
    certification_country: Optional[str] = None
    include_adult: Optional[bool] = False
    include_video: Optional[bool] = False
    primary_release_year: Optional[int] = None
    primary_release_date_gte: Optional[str] = None
    primary_release_date_lte: Optional[str] = None
    region: Optional[str] = None
    release_date_gte: Optional[str] = None
    release_date_lte: Optional[str] = None
    vote_average_gte: Optional[float] = None
    vote_average_lte: Optional[float] = None
    vote_count_gte: Optional[float] = None
    vote_count_lte: Optional[float] = None
    watch_region: Optional[str] = None
    with_cast: Optional[str] = None
    with_companies: Optional[str] = None
    with_crew: Optional[str] = None
    with_genres: Optional[str] = None
    with_keywords: Optional[str] = None
    with_origin_country: Optional[str] = None
    with_original_language: Optional[str] = None
    with_people: Optional[str] = None
    with_release_type: Optional[str] = None
    with_runtime_gte: Optional[int] = None
    with_runtime_lte: Optional[int] = None
    with_watch_monetization_types: Optional[str] = None
    with_watch_providers: Optional[str] = None
    without_companies: Optional[str] = None
    without_genres: Optional[str] = None
    without_keywords: Optional[str] = None
    without_watch_providers: Optional[str] = None
    year: Optional[int] = None

"""
def aiscripting():
    #load env variables from .env file
    load_dotenv()

    #get  the API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI KEY WAS NOT FOUND IN ENV")

    #initialize the openai object
    client = OpenAI(api_key=api_key)

    #send prompt
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Write a one-sentence bedtime story about iron man."}
    ]
)

    #print(response.choices[0].message.content)
    return response.choices[0].message.content
"""


@app.route('/search/<string:movieTitle>') #movieTitle is a path parameter
def search(movieTitle):
    movie = search_movie(movieTitle)
    if not movie: #movie is an empty list
        return jsonify(f"the movie {movieTitle} does not exist.")
    else: #valid movie
        #return jsonify(movie[0]["original_title"])
        return jsonify(movie)



def search_movie(movie):
    url = "https://api.themoviedb.org/3/search/movie"
    headers = {
        "Accept" : "application/json" #format we want the response data (json)
    }
    params = {
        "query" : movie,        #movie we're searching for
        "api_key": os.getenv("TMDB_API_KEY"),  #api key
        "include_adult" : True, #include adult movies
        "language" : "en-US",   #english language
        "page" : 1              #only 1 page of results
    }

    response = requests.get(url,headers=headers,params=params)

    if response.status_code == 200: 
        #200 means the request was successful
        data = response.json()
        return data['results']
    else:
        print("error:", response.status_code) #went wrong
        return []



#ensures app is not restart manually if any changes are made in code
if __name__ == '__main__':
    #runs app in debug mode
    app.run(debug=True)

