# Tracey

Tracey is a visualization tool specifically made for investigative journalists to explore relationships between people
they investigate.

In our case, we parsed 50 transcripts of videos exploring the deep connections between politicians in Romania. To view our final visualization, run the streamlit app and go to the tab "View 50 Video Visualization".

### How to run the app

1. Clone the repository
2. Build the docker image: ```docker build tracey:0.0.1 Dockerfile-prod .```
3. Run the docker image and port-forward the Streamlit application: ```docker run -d -p 8501:8501 tracey:0.0.1```

In order to access all features, you should have a service-google-account.json key, setup a google api key and project and set the following environment variables, in a .env environment:

GOOGLE_API_KEY="" 
GEMINI_API_KEY="" (same as GEMINI API KEY)
GOOGLE_APPLICATION_CREDENTIALS="service-google-account.json"

In order to see only the visualization, you can just set something random in the google project id section in order to
process it.

### Example part of our visualization

<img width="1390" height="668" alt="image" src="https://github.com/user-attachments/assets/3f735329-85d2-43e9-9711-1bf30b4a97d3" />

### Future design for the application

https://www.figma.com/proto/v6O9o8ZKQVNxI3b5rgmLnR/Hackathon?node-id=25-51&p=f&t=Uk8la9DznkLSBsA5-1&scaling=min-zoom&content-scaling=fixed&page-id=0%3A1&starting-point-node-id=25%3A51

### Features

1. Users can add files sequentially and see the graph being built out.
2. Users can give a folder full of txt files and the AI will build a graph from all of the information.
