/**
 * fetches current popular movies and adds a new movie slide to the movie carousel in index.html
 * @returns void
 */
function fetchPopularCarouselMoviesHomePage(){
  
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
  ;
}

  //DOMContentLoaded makes sure our JS code only runs after the HTML has been fully loaded
  //what could go wrong is elemid="movie-carousel" may not exist yet
  document.addEventListener('DOMContentLoaded', () => {
  const popMovies = document.getElementById('titlePopMovies');
  if (popMovies) { //only true if current HTML file has the id of 'titlePopMovies'
    fetchPopularCarouselMoviesHomePage();
  }
});




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

    //show a loading message as soon as the user submits a  prompt
    //this gives user feedback that it's loading
    showStatus("Fetching movie recommendations...", "loading");

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

        //when the movies are loaded, the black boarder is placed behind the movies cards
        let background_of_recs = document.getElementById("movieResults")
        Object.assign(background_of_recs.style, {
        background: "rgba(25, 25, 25, 0.8)",
        padding: "35px",
        margin: "40px auto",
        maxWidth: "1050px",
        borderRadius: "18px",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.8)",
        textAlign: "center",
        color: "#ffffff",
        backdropFilter: "blur(6px)",
        animation: "fadeInForm 1s ease forwards"
      });

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
        //once all the movie cards have finishhed loading
        //let the user know it was successful with showing the success box message
        showStatus("Movies loaded successfully!", "success");

      })

      
      .catch(err => {//handle network or server errors
        console.error("error fetching movie recs for user", err);

        //show the red error meessage if something failed
        showStatus("Something went wrong. Please try again.", "error");
      });
      

      

    }

//wait for the Document Object Model to be fully loaded
document.addEventListener("DOMContentLoaded", () => {
  //once DOM is loaded, attach the even listener to the form

  //you pass the function with no args bc then the browser calls when the form is submitted and passing event obj automatically
  const check_if_on_right_page = document.getElementById('PromptBox')
  if(check_if_on_right_page){//runs this function only if the id=PromptBox is on the HTML
    document.querySelector("form").addEventListener("submit",fetchRecommendationForUserMoviePrompt)
  }
  //attach the form submission evebt to the custom handler function
})




/**
 * shows a status message on the screen (success, loading, error)
 * message: the text you want to display
 * type: type of message (success, error, loading), defaults to 'success'
 * duration: how long to show the message (in ms)
 * @returns void
 */
function showStatus(message, type = "success", duration = 3000) {
  //get the status message box
  const statusBox = document.getElementById("statusMessage");

  // Clear any previous styles
  statusBox.className = '';

  //add a new class based on the type(status-success or status-error)
  statusBox.classList.add(`status-${type}`);

  //set the text inside the box equal to our message
  statusBox.textContent = message;

  //makes the box visible
  statusBox.style.display = 'block';

  // if the type is not 'loading', hide the box after x amount of time
  if (type !== 'loading') {
    setTimeout(() => {
      //hide the message in the box after duration
      statusBox.style.display = 'none';
    }, duration);
  }
}












/**
 * Enables toggling password visibility by clicking an eye icon.
 * Takes the IDs of the password input and toggle button as parameters.
 * @param passwordInputId
 * @param toggleButtonId
 * @returns void
 */
function enablePasswordToggle(passwordInputId, toggleButtonId) {
  // PasswordInput contains a reference to the HTML <input> tag with the given id
  const passwordInput = document.getElementById(passwordInputId);
  
  // TogglePasswordBtn contains a reference to the HTML <button> tag with the given id
  const togglePasswordBtn = document.getElementById(toggleButtonId);

  // Safety check: if either element is not found, stop executing this function
  if (!passwordInput || !togglePasswordBtn) return; 

  // Find the "eye open" icon inside the toggle button
  const eyeOpenIcon = togglePasswordBtn.querySelector('.eye-open');

  // Find the "eye closed" icon inside the toggle button
  const eyeClosedIcon = togglePasswordBtn.querySelector('.eye-closed');

  // Add an event listener on the eye toggle button
  togglePasswordBtn.addEventListener('click', () => {

    // We are changing the type attribute of the <input> tag:
    // type = 'text' shows the password text
    // type = 'password' hides the password text

    // Check if the current input type is 'password'
    if (passwordInput.type === 'password') {
      // Change input type to 'text' to make the password visible
      passwordInput.type = 'text';

      // Show 'eye-open' icon (remove the hidden class from eyeOpenIcon)
      eyeOpenIcon.classList.remove('hidden');

      // Hide 'eye-closed' icon (add the 'hidden' class from eyeClosedIcon)
      eyeClosedIcon.classList.add('hidden');

    } else { // passwordInput.type === 'text'
      // Change input type to 'password' to hide the password
      passwordInput.type = 'password';

      // Hide 'eye-open' icon (add the 'hidden' class from eyeOpenIcon)
      eyeOpenIcon.classList.add('hidden');

      // Show 'eye-closed' icon (remove the 'hidden' class from eyeClosedIcon)
      eyeClosedIcon.classList.remove('hidden');
    }
  });
}
//for the 'enter password'
// Wait for the page to fully load the Document Object Model (DOM)
document.addEventListener('DOMContentLoaded', () => {
  // Call the function and pass the IDs of the password input and toggle button
  enablePasswordToggle('password-login', 'toggle-password');
});

//for the 'Confirm Password'
// Wait for the page to fully load the Document Object Model (DOM)
document.addEventListener('DOMContentLoaded', () => {
  // Call the function and pass the IDs of the password input and toggle button
  enablePasswordToggle('confirm-password-login', 'confirm-toggle-password');
});








/**
 * event handling for User Registration
 * - confirms the password and confirm password arte a match before sending to server
 * - if passwords match, use data is sent to server by POST request
 * - if response is succesful, replaces the page with a response HTML that tells user an email has been sent
 * - if error occurs, it displays the the correct error message
 */
async function setUpRegisterFormHandler() {
  //get the 'confirm password' input from user data
  const confirmPasswordInput = document.getElementById('confirm-password-login');

  //only continue if the id 'confirm password' exists
  if (confirmPasswordInput) {
    //get the <form> tag
    const registerForm = document.getElementById('login-form');

    //listen for form submission
    registerForm.addEventListener('submit', async function (event) {
      event.preventDefault(); // prevent page reload

      //retrieve input values from the forms fields
      const email = document.getElementById('email-login');
      const username = document.getElementById('username');
      const password = document.getElementById('password-login');
      const confirm_password = document.getElementById('confirm-password-login');
      const error_box = document.getElementById('password-error');

      //checking if the password and confirm password is the same
      if (password.value === confirm_password.value) {
        // Clear previous errors
        password.classList.remove('error');
        confirm_password.classList.remove('error');
        error_box.textContent = '';
        error_box.style.display = 'none';

        //compact the user data into 1 dictionary
        const userData = {
          UserData: {
            email: email.value,
            username: username.value,
            password: password.value
          }
        };

        //send the User data via a POST request to backend server
        const response = await fetch('/UserRegistration', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(userData)
        });

        console.log(response.status)
        
       
        if (response.ok) {//response.ok is true only when the response status is in the range 200–299
            const html = await response.text();
            //console.log("inside fetche resposne");
            console.log("html code: " + html);
            document.body.innerHTML = html; // replace entire page body with returned HTML
          }
         else {
          //there was an error 
          const error = await response.json();
          console.log("error_msg: ", error);
          console.log("error_msg inside error obj using error key: ", error.error);
          console.log("Full error stringified:", JSON.stringify(error, null, 2));
          
          //what was returned from the backend
          const error_msg = error.error

          //if the error is the password being too short
          if(error_msg.includes("Password must be in range of 3 and 80 characters")){
            password.classList.add('error');
            confirm_password.classList.add('error');
            error_box.textContent = 'Your Password is not in 3-80 character range.';
            error_box.style.display = 'block';
          }
          //the email and username are both taken already
          if(error_msg.includes("email and username are both in use")){
            email.classList.add('error');
            username.classList.add('error');
            error_box.textContent = "Your Email and Username are already in Use!";
            error_box.style.display = 'block';
          }
          //the username is already taken
          if(error_msg.includes("Username already in use")){
            username.classList.add('error');
            error_box.textContent = "Your Username is already in Use!";
            error_box.style.display = 'block';
          }
          //the email is already taken
          if(error_msg.includes("email already in use")){
            email.classList.add('error');
            error_box.textContent = "Your Email is already in Use!";
            error_box.style.display = 'block';
          }
           //they're missing fields in the submittion
          if(error_msg.includes("missing fields")){
            email.classList.add('error');
            error_box.textContent = "You're missing either your Email, Username, or Password!";
            error_box.style.display = 'block';
          }
           //the email is invalid by its form
          if(error_msg.includes("Email error from validate_email(email)")){
            email.classList.add('error');
            error_box.textContent = "Your Email is not a valid email!";
            error_box.style.display = 'block';
          }
          //verification email couldn't send
          if(error_msg.includes("Verification email could not be sent, try again")){
            email.classList.add('error');
            error_box.textContent = "Your Verification email couldn't send, try again, or try a new email!";
            error_box.style.display = 'block';
          }
          //internal error
          if(error_msg.includes("Internal Server Error")){
            email.classList.add('error');
            error_box.textContent = "Please try another time, sorry!";
            error_box.style.display = 'block';
          }
          /** 
          else{//error message for when we don't have an if for it
            alert("Error: " + (error.error || "Unknown error"));
          }*/
        }


      } else {
        //if the passwords don't match, show error
        password.classList.add('error');
        confirm_password.classList.add('error');
        error_box.textContent = 'Your passwords do NOT match.';
        error_box.style.display = 'block';
      }
    });
  }
}
//run the function after the entire HTML page has been loaded
document.addEventListener("DOMContentLoaded", setUpRegisterFormHandler);







/**
 * event handling the User Login
 * - confirms the password and confirm password arte a match before sending to server
 * - if passwords match, use data is sent to server by POST request
 * - if response is succesful, replaces the page with a response HTML that tells user an email has been sent
 * - if error occurs, it displays the the correct error message
 */
async function UserLoginHandler() {
  //make sure its the login page
  const verify_its_login_page = document.getElementById('LOGIN-PAGE');

  //we are on the login page when true
  if (verify_its_login_page){
    //the form on the login page
    const login_form = document.getElementById('login-form');

    login_form.addEventListener('submit', async function (event) {
      event.preventDefault(); //prevent from page to reload

      //retrive the email
      const email = document.getElementById('email-login');
      //retrieve the password
      const password = document.getElementById('password-login');

      //retrive error display
      const error_display = document.getElementById('password-error')

      const UserData = {"UserData" : {"email": email.value, "password" : password.value}};
      
      //sent the userData via a POST request to backend server
      const response = await fetch('/UserLogin', {
        method: 'POST',
        headers : {"Content-Type" : "application/json"},
        body: JSON.stringify(UserData),
        credentials: "include"  // tells browser to send cookies for sessions
      });

      console.log(response.status);

      const result = await response.json();

      if (result.success){
        window.location.href = '/home';
      }else{
        const error_text = result.error
        if(error_text.includes('This Email Is Not Registered')){
          email.classList.add('error')
          error_display.style.display = 'block'
          error_display.textContent = error_text
        }
        if(error_text.includes('The Password Entered Is Incorrect')){
          password.classList.add('error')
          error_display.style.display = 'block'
          error_display.textContent = error_text
        }
        if(error_text.includes('Your Account Was Never Verified, Check Your Email')){
          password.classList.add('error')
          error_display.style.display = 'block'
          error_display.textContent = error_text
        }
        //alert(result.error);
      }



    })

  }
}
//run the UserLoginHandler() when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", UserLoginHandler);