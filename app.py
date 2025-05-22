from openai import OpenAI
from flask import Flask, jsonify
import os
from dotenv import load_dotenv
import requests

#app object resprents our web app, instance of flask class
app = Flask(__name__)


#this route decorator connects this url to homeFunc()
@app.route('/') #string inside is the URL path: https://localhost:5000/
def homeFunc():
    return aiscripting()
    #return "welcome to the home page of this movie proj"
    #whatever is returned is what the visitor sees in their browser


@app.route('/search/<string:movieTitle>') #movieTitle is a path parameter
def search(movieTitle):
    movie = search_movie(movieTitle)
    if not movie: #movie is an empty list
        return jsonify({"error": f"the movie {movieTitle} does not exist."})
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

#ensures app is not restart manually if any changes are made in code
if __name__ == '__main__':
    #runs app in debug mode
    app.run(debug=True)

