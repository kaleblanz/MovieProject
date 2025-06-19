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

#SQLAlchemy will translate our python commands into SQL and PostgreSQL server runs them
from db import SessionLocal
from models import Users
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from email_validator import validate_email, EmailNotValidError

#limit repeated requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

#for sending mail verification
from flask_mail import Mail, Message
from email_verification import confirmToken, generateConfirmationToken



#request vs requests:
#request from Flask is for incoming HTTP requests to my flask server
#requests from python lib is for sending HTTP requests to other API's or Servers

#app object resprents our web app, instance of flask class
app = Flask(__name__)


load_dotenv()

app.config['MAIL_SERVER'] = 'smtp.gmail.com' #the SMTP server
app.config['MAIL_PORT'] = 587 #port for TLS encryption
app.config['MAIL_USE_TLS'] = True #enable TLS (Transport Layer Security)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') #my email address
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') #my password for said email
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']
print("the app,configs:")
print("app.config['MAIL_USERNAME'] : ", app.config['MAIL_USERNAME'])
print("app.config['MAIL_PASSWORD'] : ", app.config['MAIL_PASSWORD'])
print("app.config['MAIL_DEFAULT_SENDER'] : ", app.config['MAIL_DEFAULT_SENDER'])

    
    #return None

#init Flask-Mail obj with app
mail = Mail(app)


#to limit requests
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"] #global limits
)

GENRES_ALIASES = {
    "sci-fi": "Science Fiction",
    "scifi": "Science Fiction",
    "sf": "Science Fiction",
    "romcom": "Romance",
    "kids": "Family",
    "children": "Family",
    "suspense": "Thriller",
    "doc": "Documentary",
    "animated": "Animation",
    "bio": "Biography",
    "psychological thriller": "Thriller",
    "superhero": "Action",
    "superheroes": "Action",
    "sci fi": "Science Fiction",
    "sci_fi": "Science Fiction",
    "romantic" : "Romance"
}

REASON_TMDB = 1
REASON_SIMILIAR = 2
REASON_NEGATION = 3

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


@app.route('/login')
def loginPage():
    """
    renders the login page for user to login
    """
    return render_template("login.html")

@app.route('/register')
def registerPage():
    """
    render the register page for a user to createe their new account
    """
    return render_template('register.html')




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
        "sort_by" : "popularity.desc",
        "vote_count.gte" : 150

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
    print('the users prompt: ',userPrompt)
    flag,movie_data = direct_user_prompt(userPrompt)
    #flag variable describes which prompt was taken
    #flag= 1 -> uses the TMDB search
    #flag= 2 -> uses our similiar method using GPT 4o
    #flag= 3 -> uses multiple checks and searches using GPT 4o and language checks
    if flag == 1:
        recommendation = discoverUsersRecommendationFromPrompt(movie_data)
        if not recommendation or len(recommendation) == 0:
            return jsonify({
            "movies": [],
            "flag": flag,
            "error": "No movies found from TMDB."
        }), 500
        print("recommendation: ", recommendation)

        movies = []
        for movie_i in range(min(len(recommendation), 4)):
            movies.append(recommendation[movie_i])

        return jsonify({
            "movies" : movies,
            "flag" : flag
        })

    elif flag == 2: 
        similar_movies = searchSimilarMoviesTMDB(movie_id=search_movie(movie=movie_data)['id'])
        #print(f"movies similiar to: {movie_data} are: {similar_movies}")
        if not similar_movies or len(similar_movies) == 0:
            return jsonify({
            "movies": [],
            "flag": flag,
            "error": "No movies found from TMDB."
        }), 500

        movies = []
        for movie_i in range(min(len(similar_movies), 4)):
            movies.append(similar_movies[movie_i])

        return jsonify({
            "movies" : movies,
            "flag" : flag
        })


    else: #flag = 3
        movies = []
        print("movie_data loads: ",json.loads(movie_data))
        movies_from_movie_data = json.loads(movie_data)['movies']
        print(f"flag: {flag}, and the movie_data: {movie_data}")
        for movie in movies_from_movie_data:
            movie_info = search_movie(movie=movie)
            movies.append(movie_info)
    
        return jsonify({
            "movies" : movies,
            "flag" : flag
        })


def direct_user_prompt(userPrompt: str):
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

    if contains_negation(userPrompt):
        for attempt in range(3):
            result = GPT_PROMPT3(client=client, userPrompt=userPrompt)
            if "error" not in result:
                return REASON_NEGATION, result
            print(f"PROMPT3 failed on attempt {attempt+1}")
        print(f"Falling back to PROMPT1 after PROMPT3 failures for prompt: {userPrompt}.")
        return REASON_TMDB,GPT_PROMPT1(client=client, userPrompt=userPrompt)

    if IsUserLookingForSimiliarMovies(user_prompt=userPrompt):
        return REASON_SIMILIAR,GPT_PROMPT2(client=client, userPrompt=userPrompt)

    return REASON_TMDB,GPT_PROMPT1(client=client, userPrompt=userPrompt)



def GPT_PROMPT1(client: OpenAI, userPrompt: str):
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
            "do NOT try to match filters or fill any fields. Instead, leave all fields as `None`."

            "Only use official TMDB genre names. Do not combine genres into hybrid names like 'Romantic Comedy' or 'Action-Comedy'."
            "Use only genres from this list exactly as shown:  "
            "Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, TV Movie, Thriller, War, Western."
            },
            
            {"role": "user", "content": userPrompt}
        ],
        text_format = MovieFormatter #where my pydantic baseModel is used
    )
    print('Prompt 1:', response.output_parsed)
    
    movie_data = callAllHelperFunctionsToConvertAttributrestoID(response.output_parsed)

    #returns an instance of my MovieFormatter Pydantic Model with the ID's as values
    return movie_data




def GPT_PROMPT2(client: OpenAI, userPrompt: str):
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
    return response.output_text

def GPT_PROMPT3(client: OpenAI, userPrompt: str):
    #to disect the user's prompt 
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role":"system",
                "content" : (
                "You are a movie expert. You will be given a natural language prompt from a user about what movies they want recommended. "
                "You will carefully extract structured information from the prompt and fill in the appropriate values of this JSON Dictionary. "
                "If a field does not apply or is not mentioned, set it to an empty list ([]) or empty string (\"\") as appropriate. "
                "You must return EXACTLY one JSON object and nothing else. Do not include any explanation or additional text.  \n\n"
                "Here is the JSON format to fill:\n"
                "{\n"
                '  "include_genres": [],\n'
                '  "exclude_genres": [],\n'
                '  "include_people": [],\n'
                '  "exclude_people": [],\n'
                '  "include_keywords": [],\n'
                '  "exclude_keywords": [],\n'
                '  "include_directors": [],\n'
                '  "exclude_directors": [],\n'
                '  "include_movies": [],\n'
                '  "exclude_movies": [],\n'
                '  "tone": "",  // e.g. dark, uplifting, funny, feel-good\n '
                '  "decade": "",\n'
                '  "release_year": "",\n'
                '  "language": "",\n'
                '  "country": "",\n'
                '  "include_runtime_minutes": "",\n'
                '  "minimum_rating": "",\n'
                '  "include_certification": "",\n'
                '  "exclude_certification": "",\n'
                '  "include_companies": [],\n'
                '  "exclude_companies": [],\n'
                '  "notes": ""  // any extra user desires that don\'t fit above fields \n'
                "}\n"
            )
            },
            
                {
                    "role": "user",
                    "content": userPrompt
                }
        ]
    )

    result_of_disecting = response.choices[0].message.content
    
    #in the future, you have to handle these return statements for when this functions returns
    if not result_of_disecting.strip():
        print("GPT returned empty content")
        return {"error":"GPT returned empty result"}
    try:
        result_of_disecting = json.loads(result_of_disecting)
        print('result of inspection:', result_of_disecting)
    except json.JSONDecodeError as e:
        print(f"WARNING: JSON decode error: {e} — content was: {result_of_disecting}")
        return {"error": "Invalid JSON in dissection result"}

    

    response = client.chat.completions.create(
            model="gpt-4o",
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a movie expert.\n"
                        "You will be provided with a JSON object that contains structured user preferences and exclusions for a movie recommendation task.\n"
                        "You must strictly respect the user's constraints:\n"
                        "- DO NOT include any movie that features people listed in 'exclude_people' (in any capacity: starring, supporting, cameo, uncredited).\n"
                        "- DO NOT include any movie directed by anyone in 'exclude_directors'.\n"
                        "- Strongly prefer movies that match 'include_genres', 'include_people', 'include_keywords', 'tone', 'decade', 'release_year', 'language', 'country', 'minimum_rating', and other specified preferences.\n"
                        "- Movies with 'exclude_genres', 'exclude_keywords', 'exclude_companies', or 'exclude_certification' must also be excluded.\n"
                        "- If you are unsure about a movie's cast, crew, or other matching criteria, DO NOT include it.\n"
                        "You must return EXACTLY 4 movie titles ONLY, and nothing else.\n"
                        "Return only in this format:\n"
                        "{\"movies\": [\"Title1\", \"Title2\", \"Title3\", \"Title4\"]}\n"
                        "Do not include any other text, explanation, or commentary.\n"
                        "If you break this rule, you will fail your task."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(result_of_disecting, indent=2)
                }
            ],
            temperature=0.1
            #temperature is the creative control for langauge generatrion 0-2, deterministic-very creative
        )
    result = response.choices[0].message.content
    result_loads =json.loads(result)
    print('response of Prompt 3:', result_loads)

    #JSON does not support sets so i turn it into a list
    invalid_movies = list(validateGPTPrompt3Response(exclude_people=result_of_disecting['exclude_people'],exclude_directors=result_of_disecting['exclude_directors'], 
                                                     exclude_movies=result_of_disecting['exclude_movies'], included_people=result_of_disecting['include_people'],result=result_loads))
    print('invalid movies after:', invalid_movies)

    #true when there are no invalid movies
    if not invalid_movies:
        return result
    
    response = client.chat.completions.create(
            model="gpt-4o",
            messages = [
                {
                    "role": "system",
                    "content": (
                    "You are a strict movie recommendation validator.\n"
                    "You will be given the original user request, your previous list of recommended movies, and a list of movies from your response that VIOLATED the user's exclusions.\n"
                    "Your task is to re-generate a new list of 4 movies that strictly adheres to the user's constraints, avoiding any previously incorrect movies.\n"
                    "Do NOT include any movies that were in the 'incorrect_movies' list.\n"
                    "You must follow these rules:\n"
                    "- Do NOT include any movie featuring people in 'exclude_people' in any capacity (main, supporting, cameo, uncredited).\n"
                    "- Do NOT include any movie directed by people in 'exclude_directors'.\n"
                    "- Strongly prefer movies matching the positive preferences.\n"
                    "- If unsure about a movie's cast or crew, DO NOT include it.\n"
                    "You must return EXACTLY 4 movie titles ONLY, and nothing else.\n"
                    "Return only in this format:\n"
                    "{\"movies\": [\"Title1\", \"Title2\", \"Title3\", \"Title4\"]}\n"
                    "If you break this rule, you will fail your task."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps({
                    "original_user_prompt": userPrompt,
                    "parsed_preferences": result_of_disecting,
                    "previous_response_movies": result_loads,
                    "incorrect_movies": invalid_movies
                }, indent=2)
                }
            ],
            temperature=0.1
            #temperature is the creative control for langauge generatrion 0-2, deterministic-very creative
        )
    
    second_attempt_result = response.choices[0].message.content
    second_attempt_result = json.loads(second_attempt_result)
    print("second_attempt_result: ", second_attempt_result)
    return second_attempt_result


def validateGPTPrompt3Response(exclude_people:list, exclude_directors:list, exclude_movies:list, included_people:list, result: dict)->set:
    movie_list = result['movies']
    invalid_movies = set()

    excluded_people_set = set(people.strip().lower() for people in exclude_people)
    excluded_directors_set = set(director.strip().lower() for director in exclude_directors)

    for movie in movie_list:
        if movie in exclude_movies:
            invalid_movies.add(movie)
        search_result = search_movie(movie=movie)
        if not search_result:
            print(f"skip validation for {movie}")
            continue
        #print("movie break:", movie)
        #print("search_movie(movie=movie)['id']:",search_movie(movie=movie)['id'])

        cast_list,director_list = searchCreditsTMDB(search_result['id']) 

        #lowercase all the names
        cast_set = set(name.lower() for name in cast_list)
        director_set = set(name.lower() for name in director_list)

        #check if any excluded person is in the cast
        if excluded_people_set & cast_set:
            invalid_movies.add(movie)
        
        #check if any excluded director is in the excluded_director
        if excluded_directors_set & director_set:
            invalid_movies.add(movie)
        
        #for people in included_people:
            #if people not in cast_list:
                #invalid_movies.add(movie)
    
    return invalid_movies

def IsUserLookingForSimiliarMovies(user_prompt):
    user_prompt = user_prompt.lower()
    if "similar" in user_prompt or "like" in user_prompt:
        return True
    else:
        return False\

def contains_negation(userPrompt: str):
    neg_keywords = [
    " no ",
    " not ",
    " without ",
    " exclude ",
    " excluding ",
    " except ",
    " avoid ",
    " don't include ",
    " do not include ",
    " skip ",
    " omit ",
    " leave out ",
    " minus ",
    " nothing with ",
    " none of ",
    " ban ",
    " prohibit ",
    " never include ",
    " remove ",
    " nothing ",
    " nothin ",
    " notin "
]
    userPrompt_lowered = userPrompt.lower()
    return any(keyword in userPrompt_lowered for keyword in neg_keywords)


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

def normalize_genres(genre_name: str):
    return GENRES_ALIASES.get(genre_name.lower(),genre_name)

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

def searchCreditsTMDB(movie_id: int):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    headers = {"Accept" : "application/json"}
    params = {
        "query" : movie_id,        #movie we're searching for
        "api_key": os.getenv("TMDB_API_KEY"),  #api key
        }
    
    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")

    response = response.json()

    cast_results = [movie['name'] for movie in response.get('cast',[])]
    director_results = [movie['name'] for movie in response.get('crew',[]) if movie.get("job") == "Director"]

    return cast_results,director_results



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

    genre_after_aliase_check = normalize_genres(genre_name=genre)

    for dict_genre in results:
        if dict_genre['name'].upper() == genre_after_aliase_check.upper():
            return dict_genre['id']
            
    raise ValueError(f"this genre cannot be found: {genre_after_aliase_check}")

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
    params={"api_key" : os.getenv("TMDB_API_KEY"), "vote_count.gte" : 150, "sort_by" : "vote_average.desc"} 

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

def searchSimilarMoviesTMDB(movie_id: int):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations"
    #url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    headers = {"Accept" : "application/json"}
    params = {"api_key" : os.getenv("TMDB_API_KEY"), "vote_count.gte" : 150}

    response = requests.get(url,headers=headers,params=params)

    if response.status_code != 200:
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")
    
    result = response.json()

    result = result.get('results',[])

    if not result:
        print("TMDB has no similar movies")
        return []
    
    return result



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

    if response.status_code != 200: 
        raise RuntimeError(f"TMDB error {response.status_code}: {response.text}")
    
    result = response.json()
    results = result.get("results",[])

    if not results:
        #no result for this movie
        print(f"WARNING: No TMDB result found for movie: {movie}")
        return None

    for result in results:
        if result['title'].lower() == movie.lower():
            return result

    print(f"WARNING: Using first TMDB result for movie: {movie}")
    return results[0]


#create a new session (our connection to the PostgreSQL DB)
db = SessionLocal()

@app.route('/UserRegistration', methods=['POST'])
@limiter.limit("5 per minute")
def handleUserRegistration():
    #pp()
    print("inisdeeee")
    #parse incoming JSON data from client side
    user_data = request.get_json().get('UserData')
    print('user_datap: ', user_data)
    #verifies that all keys are in the user_data dict
    required_fields = ['email','username','password']
    missing = [field for field in required_fields if field not in user_data]
    if missing:
        return jsonify({"error" : f"missing fields: {missing}"}), 400
    
    #validates the email is proper form
    email = user_data['email']
    print("error with emails userdata: ", user_data)
    print("error with email: ", email)
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return jsonify({"error" : "Email error"}), 400
    
    #validates the password is proper length
    password = user_data['password']
    if len(password) < 3 or len(password) > 80:
        return jsonify({"error": "Password must be in range of 3 and 80 characters"}), 400
    

    username = user_data['username']
    print(f"email : {email},   username: {username},   password: {password}")

    #use a context manager to create and automatically close the DB session
    with SessionLocal() as db:
        #check if email or username is already exists in DB
        existing_user = db.query(Users).filter(
            (Users.email == email) | (Users.username == username)
        ).first()#get the first matching user, or None if no match

        if existing_user:
            #if an existing user with the same email is found
            if existing_user.email == email:
                print("erorr:  Email already in use 400")
                return jsonify({"error" : "Email error"}), 400
            #if an existing user with the same username is found
            else:
                print("erorr:  username already in use 400")
                return jsonify({"error" : "Username already in use"}), 400
        
        #we can continue knowing we have a unique username and email

        #create a new User Obj
        hash_password = generate_password_hash(password)
        new_user = Users(
            username = username,
            email = email,
            password_hashed = hash_password,
            date_created = datetime.now(timezone.utc),
            profile_picture = "",
            last_login = datetime.now(timezone.utc),
            active_status = True
        )

        try:
            #add 'new_user' to session
            db.add(new_user) 

            #commit the transaction (saves to DB)
            db.commit()

            print(f"User successfully added with ID: {new_user.id!r}")


            #email confirmation token and email
            token = generateConfirmationToken(email=email)
            #change BASE URL EVENTUALLY WHEN CHANGING HOST
            confirmURL = os.getenv("BASE_URL","http://localhost:5000")
            confirmURL += f"/verify-email?token={token}"
            
            msg = Message("Confirm Your Email to continue", 
                          sender=app.config['MAIL_USERNAME'] ,
                          recipients=[email])
            msg.body = f"Welcome {username}! Click the link to verify your email: {confirmURL}"
            print("email sending")
            mail.send(message=msg)
            print("enail send")

            #print(str(render_template("notice_email.html", email=email)))
            return render_template("notice_email.html", email=email), 201

        
        except Exception as e:
            print("error during DB operation", e)
            db.rollback() #un-does all changes i've made in the current DB since the last commit()
            return jsonify({"error": "Internal Server Error"}),500
        
        #readUserTable()
        
        '''
        return jsonify({
            "success": True,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        }), 201
        '''
    

@app.route('/verify-email')
def verifyEmail():
    token =  request.args.get('token')
    email = confirmToken(token=token)

    if not email:
        return "Verification link is invalid or expired.", 400
    
    with SessionLocal() as db:
        user = db.query(Users).filter(Users.email == email).first()

        if not user:
            return "User not found", 404
        
        if user.is_verified:
            return "Account is already verified!", 200
        
        user.is_verified = True
        db.commit()
        print(f"the user: {user.username} has been added and rendering the template of verify_success.html")
        return render_template("verify_sucess.html", email=email), 200
        


def readUserTable():
    with SessionLocal() as db:
        users = db.query(Users).all()
        for user in users:
            print(user)

#ensures app is not restart manually if any changes are made in code
if __name__ == '__main__':
    #runs app in debug mode
    app.run(debug=True)

