## Application Documentation

This documentation provides an overview of the application and explains the purpose of each route and function within the code.

### Overview

The application is a URL shortener web application built using Flask, a Python web framework. It allows users to create shortened URLs and track the number of visits to those URLs. Users can register an account, log in, and access their personalized dashboard to manage their shortened URLs. The application also provides analytics for each shortened URL, displaying the visit locations(currently restricted to Oregon, US. because of current hosting) and devices used.

### Dependencies

The following dependencies are required to run the application:

- Flask: A Python web framework used for developing the web application.
- Flask-Migrate: A Flask extension for database migrations.
- SQLAlchemy: A Python SQL toolkit and Object-Relational Mapping (ORM) library.
- Flask-Login: A Flask extension that provides user session management and authentication.
- ip2geotools: A Python library for geolocating IP addresses.
- Flask-Limiter: A Flask extension for rate limiting requests.
- Redis: A data structure server used for caching and storage.
- user-agents: A Python library for parsing user agent strings.
- validators: A library for validating and sanitizing URLs.

### File Structure

The main file of the application is `main.py`, which contains all the routes and functions. Here is an overview of the file structure:

- Import statements for required modules and libraries.
- Configuration and setup for Flask, database, Redis, and other extensions.
- Definition of database models (Link, VisitLocation, User) using SQLAlchemy.
- Login manager configuration and user loader function.
- Route handlers and functions for different parts of the application.

### Routes and Functions

Below is a description of each route and function in the application:

1. **Route: '/'** (Home page route)
   - Method: GET, POST
   - Purpose: Renders the index.html template, which represents the home page of the application.

2. **Route: '/register'** (Signup Route)
   - Method: GET, POST
   - Purpose: Handles user registration. If a POST request is received, it validates the user input, creates a new user account, and stores it in the database. If the input is invalid or a user with the same username/email already exists, appropriate error messages are displayed.

3. **Route: '/login'** (Login Route)
   - Method: GET, POST
   - Purpose: Handles user login. If a POST request is received, it validates the user input, checks if the user exists in the database, and verifies the password. If the login is successful, the user is redirected to the dashboard page. Otherwise, appropriate error messages are displayed.

4. **Route: '/logout'** (Route to logout)
   - Method: None (GET)
   - Purpose: Logs out the currently logged-in user and redirects them to the home page.

5. **Route: '/dashboard/<<string:username>>'** (Dashboard page route)
   - Method: GET, POST
   - Purpose: Renders the dashboard.html template, which represents the user dashboard. If a POST request is received, it handles the creation of shortened URLs. It validates the original URL, generates a short URL (either randomly or using a custom alias), checks for duplicates, saves the URL and associated details in the database, and generates a QR code image for the short URL. The POST request to generate a short url is limited to 10 per day and the data of the limiter is saved to redis cache.

6. **Route: '/<<string:shortUrl>>'** (Route to direct short URL to original)
   - Method: GET
   - Purpose: Redirects the user to the original URL associated with the given short URL. Also tracks visit statistics by storing the visitor's IP address, location, visit time, and device in the database.

7. **Route: '/history/<<string:user>>'** (Route to view user link history)
   - Method: GET
   - Purpose: Renders the history.html template, which displays a user's link history. Retrieves all links associated with the specified user from the database and passes them to the template for display.

8. **Route: '/analytics/<<int:id>>/'** (Route to view link analytics)
   - Method: GET
   - Purpose: Renders the analytics.html template, which displays link analytics for a specific link using link ID. Retrieves the link details, associated QR code image, and visit data from the database and passes them to the template for display.

9. **Route: '/delete/<<int:id>>/'** (Route to delete link)
   - Method: GET
   - Purpose: Deletes a link and its associated visit statistics from the database by link ID. It verifies that the current user owns the link before deleting. After deletion, the user is redirected to their dashboard page.

## License
Under [MIT](https://github.com/Igbinosa-Christian/scissorapp/blob/main/LICENSE.md)

## Contact
- [Twitter](https://twitter.com/_m_anor)
- Email igbinosa62@gmail.com
- [Project Repository](https://github.com/scissorapp)
