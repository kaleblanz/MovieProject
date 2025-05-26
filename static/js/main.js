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
              <h2>${movie.title}</h2>
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
      .catch(err => console.error("Error loading movies:", err));
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
  submissionEvent.preventDefault()//this prevents the page from reloading
}
