from openai import OpenAI
from flask import Flask, jsonify, render_template, url_for,redirect, request
import os
from dotenv import load_dotenv
import requests
import json

#for our MovieFormatter Object
from pydantic import BaseModel 
from typing import Optional

#for splitting a string with mutiple characters
import re


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
        "page" : 1,
        "sort_by" : "popularity.desc"
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
    flag,movie_data = sendingPromtToGPT(userPrompt)
    #flag variable describes which prompt was taken
    #flag= -> 
    #flag= -> 
    if flag == 1:
        pass

    else: #flag = 0
        pass

    #print(movie_data)
    #print(discoverUsersRecommendationFromPrompt(movie_data))
    return jsonify(userPrompt) 


def sendingPromtToGPT(userPrompt):
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


    #Prompt 1
    response = client.responses.parse(
        model = "gpt-4o",
        input = [
            {"role" : "system", "content": 
            "You're a movie search assistant. Your job is to convert the user's natural language movie request "
            "into a structured JSON object that matches the MovieFormatter BaseModel for the TMDB Discover Get Method. "
            "AND/OR Logic: comma's (,) are treated like an AND query while pipe's (|) are treated like an OR. "
            "If the user refers to actors or actresses (people seen in the movie), always use 'with_cast' — even when 'AND' or 'OR' is used."
            "Use 'with_crew' if the user specifies a specific behind-the-scenes role such as composer, editor, or cinematographer."
            "When assigning a value to 'with_crew', extract only the person's name (e.g., from 'music by Hans Zimmer', use 'Hans Zimmer')."
            "Use 'with_people' only when the person is mentioned without a specific job title or when the role is general, like 'director', 'producer', or 'creator'."
            "(for genres, cast, crew, people, watch_providers, companies, and keywords, keep them in their string form and don't turn them into their ID equivalent): "
            "certification, certification.gte, certification.lte, certification_country, "
            "include_adult, include_video, primary_release_year, primary_release_date.gte, primary_release_date.lte, region,"
            "release_date.gte, release_date.lte, vote_average.gte, vote_average.lte, vote_count.gte, vote_count.lte, watch_region, with_cast, with_companies,"
            "with_crew, with_genres, with_keywords, with_origin_country, with_original_language, with_people, with_release_type, with_runtime.gte,"
            " with_runtime.lte, with_watch_monetization_types, with_watch_providers, without_companies, without_genres, without_keywords,"
            "without_watch_providers, year. "
            "Format your response strictly as a JSON object that fits the MovieFormatter BaseModel, do include extra text or explanation."

            "If the users prompt is asking for movies 'similar to' or 'like' another movie (example: 'give me a movie similar to Fight Club'), "
            "do NOT try to match filters or fill any fields. Instead, leave all fields as `None`."},
            
            {"role": "user", "content": userPrompt}
        ],
        text_format = MovieFormatter #where my pydantic baseModel is used
    )
    print('Prompt 1:', response.output_parsed)
    
    movie_data = callAllHelperFunctionsToConvertAttributrestoID(response.output_parsed)

    #all() returns true if every value iterating is truthy, o/w false
    #getattr(obj, attr), returns the value of obj.attr
    all_attributes_none = all(
        getattr(movie_data,attribute) is None
        for attribute in movie_data.model_dump().keys()
    )

    #if not all the attributes of our pydantic object is 'None'
    if not all_attributes_none:
        #if true then we will use Prompt 1 for user's rec
        #returns an instance of my MovieFormatter Pydantic Model with the ID's as values
        return 1,movie_data
    
    #else if for when we run our Prompt 1 and our pydantic object had all 'None' for it's attributes
    else:
        if IsUserLookingForSimiliarMovies(userPrompt):
            #when we true we know the user is looking for a movie similiar to another
            #Prompt 2
            response = client.responses.parse(
                model = "gpt-4o",
                input=[
                    {"role" : "system", "content" :  "You're a movie search assistant, extract the name of the movie title"
                    "that the user is looking for a similar movie too."
                    "For example: 'Recommend me a movie that is similiar/like the film Inception'. You would then just return 'Inception' as a string."
                    "If a user lists mutliples movies in their prompt, use your judegment and return the most popular movie."
                    "No explantion or extra text, just the movie title."},
                    {"role":"user", "content":userPrompt}
                ]
            )
            #returns just the title of the movie the user wants a similiar movie too
            print('response of Prompt 2:',response.output_text)
            return 2,response.output_text
        
        else:
            #Prompt 3
            #We use this as our last stand for when our other 2 Prompts don't have a suffice answer for the user
            response = client.responses.parse(
                    model = "gpt-4o",
                    input=[
                        {"role" : "system", "content" :   
                        "You are a movie recommendation assistant. Return exactly 4 movie titles, as a single string with no spaces and no extra text. "
                        "Format: Title1,Title2,Title3,Title4\n"
                        "If the user says 'not with X' or 'not directed by Y', you must exclude any movie involving that person X and Y in any role. "
                        "Do not include any movie that violates the user's exclusions. No explanations. Only the 4 valid titles. "
                        "DO NOT include any movies involving Leonardo DiCaprio or Tom Hanks. Double-check every movie title. If it violates this rule, do NOT include it."


                        
                        },

                        {"role":"user", "content":userPrompt}
                    ]
                )
            
            print('response of Prompt 3:',response.output_text)
            return 3,response.output_text


def IsUserLookingForSimiliarMovies(user_prompt):
    user_prompt = user_prompt.lower()
    if "similar" in user_prompt or "like" in user_prompt:
        return True



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

def callAllHelperFunctionsToConvertAttributrestoID(movie_data: MovieFormatter):
    """
    calls the respective search function for the respective attribute of our pydantic model MovieFormatter
    """
    movie_data.with_cast = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_cast,searchPersonIDTMDB)
    movie_data.with_crew = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_crew,searchPersonIDTMDB)
    movie_data.with_people = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_people,searchPersonIDTMDB)

    movie_data.with_companies = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_companies,searchCompanyIDTMDB)
    movie_data.without_companies = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.without_companies,searchCompanyIDTMDB)

    movie_data.with_genres = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_genres,searchGenreIDTMDB)
    movie_data.without_genres = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.without_genres,searchGenreIDTMDB)

    movie_data.with_keywords = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_keywords,searchKeyWordIDTMDB)
    movie_data.without_keywords = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.without_keywords,searchKeyWordIDTMDB)

    movie_data.with_watch_providers = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.with_watch_providers,searchProviderIDTMDB)
    movie_data.without_watch_providers = convertStringToIDEquivalentForMovieFormatterAttributes(movie_data.without_watch_providers,searchProviderIDTMDB)

    #returns updated instance of our pydantic model
    return movie_data

    
def convertStringToIDEquivalentForMovieFormatterAttributes(input, searchTMDBFunction):
    """
    we are converting the cast/crew/people/(w/wo)companies/(w/wo)genres/(w/wo)keywords/(w/wo) providers to their id equivalent
    when filtering movies, expects ID's not names
    handles both AND(,) and OR(|)
    """
    if input is None:
        return None
    #'([,\|])' is a regular expression that splits at comma and pipes, but also keeps them in the splitted list
    split = re.split(r'([,\|])', input)

    result = []

    for element in split:
        element = element.strip() #remove leading/trailing whitespace
        if element not in ['|',',']:
            result.append(str(searchTMDBFunction(element))) #calls the appropriate function for the MovieFormatter Attribute
        else:
            result.append(element)
    
    return ''.join(result)
    #.join is faster than concatenation of +=


def searchPersonIDTMDB(person_name):
    url = "https://api.themoviedb.org/3/search/person"
    headers = {"Accept" : "application/json"}
    params = {
        "query" : person_name,        #movie we're searching for
        "api_key": os.getenv("TMDB_API_KEY"),  #api key
        }
    #sends a GET request to TMDB api to search for a person, .json() turns into python dic
    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")
    
    response = response.json()

    #get the results key from response, return [] if results doesn't exist
    results = response.get("results",[])

    if results:
        return results[0]['id']
    else:
        raise ValueError(f"this person cannot be found: {person_name}")

def searchCompanyIDTMDB(company_name):
    url = "https://api.themoviedb.org/3/search/company"
    headers = {"Accept" : "application/json"}
    params = {
        "query" : company_name,        #company we're searching for
        "api_key": os.getenv("TMDB_API_KEY"),  #api key
        }
    #sends a GET request to TMDB api to search for a person, .json() turns into python dic
    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")
    
    response = response.json()

    #get the results key from response, return [] if results doesn't exist
    results = response.get("results",[])

    if results:
        return results[0]['id']
    else:
        raise ValueError(f"this company cannot be found: {company_name}")

def searchGenreIDTMDB(genre):
    url = "https://api.themoviedb.org/3/genre/movie/list"
    headers = {"Accept" : "application/json"}
    params = {
        "api_key": os.getenv("TMDB_API_KEY"),  #api key
        }
    #sends a GET request to TMDB api to search for a person, .json() turns into python dic
    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")
    
    response = response.json()

    #get the results key from response, return [] if results doesn't exist
    results = response.get("genres",[])

    for dict_genre in results:
        if dict_genre['name'].upper() == genre.upper():
            return dict_genre['id']
            
    raise ValueError(f"this genre cannot be found: {genre}")

def searchKeyWordIDTMDB(keyword):
    url = "https://api.themoviedb.org/3/search/keyword"
    headers = {
        "Accept" : "application/json"
    }
    params={
        "query" : keyword,
        "api_key" : os.getenv("TMDB_API_KEY")
    }

    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")
    
    response = response.json()

    results = response.get("results",[])

    for keyword_dict in results:
        if keyword_dict['name'].upper() == keyword.upper():
            return keyword_dict['id']
    
    raise ValueError(f"the keyword: {keyword} does not exist")

def searchProviderIDTMDB(provider):
    url = "https://api.themoviedb.org/3/watch/providers/movie"

    headers = {
        "Accept" : "application/json"
    }
    params={
        "api_key" : os.getenv("TMDB_API_KEY")
    }

    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")

    response = response.json()

    results = response.get('results',[])

    for provider_dict in results:
        if provider_dict['provider_name'] == provider:
            return provider_dict['provider_id']
    
    raise ValueError(f"the provider {provider} does not exist")


def discoverUsersRecommendationFromPrompt(movie_data: MovieFormatter):
    url = "https://api.themoviedb.org/3/discover/movie"
    headers = {"Accept" : "application/json"}
    params={"api_key" : os.getenv("TMDB_API_KEY")}

    #loop through all key,value pairs in movie_data with values not None
    for key,value in movie_data.model_dump().items():
        if value != None:
            params[key] = value
    
    response = requests.get(url=url,headers=headers,params=params)

    if response.status_code != 200:
        raise ValueError(f"there was no valid rec's for the moviedata:{movie_data}")
    
    response = response.json()

    results = response.get('results',[])
    #results could be list of dictionarys or empty list
    return results





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

