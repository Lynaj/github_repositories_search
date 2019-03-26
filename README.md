The application has been created using Python 3.6.7.
In order to start the application, it is recommended to create a new virtual environment:

> virtualenv env

If only virtualenv has not been installed yet, run the pip provided by your Python to satisfy this need:

> pip install virtualenv 

Once virtualenv is ready, type:

> source env/bin/activate 

into the terminal

Each and every dependency is available in the file called 'dependencies'.
Using it, one can leverage the real value of pip, using:

> pip install -r dependencies

The final step is about starting the application:

> python application.py

The web service is set up and ready to accept HTTP connections
URL format: 

> http://localhost:8051/?search_term=arrow