//DOMContentLoaded waits for HTML to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
    //sends request to flask, asking for data at /popularMovies endpoint
    fetch('/popularMovies')
        //turn response into its JSON format
        .then(response => response.json())
        //receives parsed JSON and puts it into var: data
        .then(data => {
            //data is the list of movies
            const carousel  = document.getElementById("movie-carousel");
            //carousel refers the <div> with the id of "movie-carousel"

            //goes through each movie in data
            data.results.forEach(movie => {
                //creates a new div for each movie
                const movieItem = document.createElement("div");
                movieItem.classList.add("movie-card"); //for styling CSS
                
                //fills in the text for the movieitem
                movieItem.textContent = movie.title; 

                //add the movie div to the caresoul
                carousel.appendChild(movieItem);
            });
        })
        //if error, shows in browser console
        .catch(error=>console.error("error fetching carousel movies:",error));
});