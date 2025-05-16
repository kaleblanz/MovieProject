from flask import Flask 

#app object resprents our web app, instance of flask class
app = Flask(__name__)

#this route decorator connects this url to homeFunc()
@app.route('/home') #string inside is the URL path: https://localhost:5000/home
def homeFunc():
    return "welcome to the home page of this movie proj"
    #whatever is returned is what the visitor sees in their browser

#ensures app is not restart manually if any changes are made in code
if __name__ == '__main__':
    #runs app in debug  mode
    app.run(debug=True)