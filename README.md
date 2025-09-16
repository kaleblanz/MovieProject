# CinemaPrompt

A full-stack web app I built that uses a large language model to give movie recommendations based on natural language prompts. It's a project that brings together everything from secure user authentication to dynamic front-end content, all powered by a Flask backend.

---

### **Tech Stack**

* **Backend**: Python, Flask, SQLAlchemy, PostgreSQL, ItsDangerous, Limiter, Werkzeug Security
* **Frontend**: HTML5, CSS3, JavaScript, Jinja, Swiper.js
* **APIs**: I integrated with both the OpenAI and TMDB APIs to handle the recommendation engine and movie data.

---

### **Key Features & What I Did**

* **User Management**: I designed and implemented a complete and secure user authentication system. This included handling account creation, hashing passwords for security, and setting up an email verification process to confirm user identities.

* **Building the Recommendation Engine**: The core of the app is its ability to understand what a user wants. I built the logic to take a natural language prompt, send it to the OpenAI, and use the response to find and display relevant movies from the TMDB database to fit the user's prompt.

* **Database Design**: I set up and managed a SQL database using SQLAlchemy. I created the schema and handled all the data operations for user accounts, ensuring everything was stored and retrieved efficiently.

* **Dynamic Frontend**: The user interface is built to be modern and responsive. I used JavaScript to dynamically fetch and display content, like the trending movie carousel and the recommendation results, without needing a page reload.

* **End-to-End Development**: I handled the entire project lifecycle, from initial design to final implementation. This involved everything from architecting the backend API to styling the front-end components for a great user experience.
