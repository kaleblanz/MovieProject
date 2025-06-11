/**
 * fetches current popular movies and adds a new movie slide to the movie carousel in index.html
 * @returns void
 */
function fetchPopularCarouselMoviesHomePage(){
  //DOMContentLoaded makes sure our JS code only runs after the HTML has been fully loaded
  //what could go wrong is elemid="movie-carousel" may not exist yet
  document.addEventListener("DOMContentLoaded", () => {
    //fetch the popualr movies from the flask endpoint
    fetch('/popularMovies')
      .then(response => response.json()) //parse the http into json
      .then(data => {
        //get the carouesel container where the sldies will be added
        const carousel = document.getElementById("movie-carousel");

        //loop through each moveie
        data.results.forEach(movie => {
          //create a new div to be a movie slide
          const slide = document.createElement("div");
          //add swiper-specific class for functionaltiy and styling
          slide.classList.add("swiper-slide");

          //setting the slides innerHTML to have poster, title and descrip
          slide.innerHTML = `
            <img class="movie-poster" src="https://image.tmdb.org/t/p/w500${movie.poster_path}" alt="${movie.title}">
            <div class="movie-info">
              <h3>${movie.title}</h3>
            </div>`;
            //<p>${movie.overview}</p>

          //add the finished slide product to the carousel container
          carousel.appendChild(slide);
        });

        //initialize Swiper with desired functioanlity
        new Swiper(".mySwiper", {
          slidesPerView: 3, //show 3 slides at a time 
          spaceBetween: 30, //30px between slides
          centeredSlides: true, //center slides
          loop: true, //infinite
          autoplay: {
            delay: 3000,  //advance every 3 secs
            disableOnInteraction: false, //keep autoplay running after user interaction
          },
          grabCursor: true, //change cursor to grab icon on hover
        });
      })

      //log error if fetch fails
      .catch(err => console.error("Error loading popular movies for home screen:", err));
  });
}
fetchPopularCarouselMoviesHomePage();



/**
 * js intercepts the form submission for user prompt for movie recs.
 * fetches movie rec's via flask.
 * updates the DOM with the movie cards.
 * stays dynamic and does all of this with no reloading.
 * @returns void
 */
function fetchRecommendationForUserMoviePrompt(submissionEvent){
    submissionEvent.preventDefault();//this prevents the page from reloading

    //get value from the input field with id="PromptBox"
    const userInput = document.querySelector("#PromptBox").value;


    fetch('/MovieRecForUserPrompt',{
      method: 'POST',
      headers:{
        'Content-Type':'application/json'
      },
      body:JSON.stringify({userPrompt: userInput})
      //send the user input to backend as JSON
    })
      .then(response => response.json())
      //parese the response as JSON when it comes back from the backend

      .then(data => {
        console.log("Rec movies:",data)

        //get the container to whre the movie cards will be displayed, id = "movieResults"
        const movieContainer = document.querySelector("#movieResults");

        movieContainer.innerHTML = ""; //clear old results
        
        //data.movies bc thats the key in the json dict
        data.movies.forEach(movie => {
          //create a new div to represent each single movie card
          const movie_card = document.createElement("div");

          //asign this class movie-card to all movie cards for CSS styling
          movie_card.classList.add("movie-card");

          //date of the movie was released
          const dateOfMovie = movie.release_date;

          //create a Data Object
          const dateObj = new Date(dateOfMovie)

          //format the data
          const human_readable_data = dateObj.toLocaleDateString('en-US',{
            year: "numeric",
            month : "short",
            day : "numeric"
          })

          //defines the inner html that will be dynamically be placed on the home page
          movie_card.innerHTML = `
            <img class="movie-poster" src="https://image.tmdb.org/t/p/w500${movie.poster_path}" alt="${movie.title}">
            <div class="movie-info">
              <h3>${movie.title}</h3>
              <h4>Average Rating: ${movie.vote_average}</h4>
              <h4>Release Date: ${human_readable_data}</h4>
              <p>${movie.overview}</p>
              <button class="toggle-button">Show More</button>
            </div>`;
          
          //get the "Show More" button tjat was added to the movie card
          const toggleButton = movie_card.querySelector(".toggle-button");
          
          //add a click event to the button so it can expand/collapse the movie descrip
          toggleButton.addEventListener("click", () => {
            //togggle the "expand" class on the movie card
            movie_card.classList.toggle("expanded");

            //change button text based on wheteher the card is expanded or not
            toggleButton.textContent = movie_card.classList.contains("expanded")
             ? "Show Less" : "Show More";
          });

          //add the finished movie card product to the movieContainer div to the html page
          movieContainer.appendChild(movie_card);
        });
      })

      
      .catch(err => console.error("error fetching movie recs for user", err));
      //handle network or server errors
}

//wait for the Document Object Model to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
  //once DOM is loaded, attach the even listener to the form

  //you pass the function with no args bc then the browser calls when the form is submitted and passing event obj automatically
  document.querySelector("form").addEventListener("submit",fetchRecommendationForUserMoviePrompt)
  //attach the form submission evebt to the custom handler function
})