# Tracey

Tracey is a visualization tool specifically made for investigative journalists to explore relationships between people
they investigate.

In our case, we parsed 50 transcripts of videos exploring the deep connections between politicians in Romania. To view our final visualization, run the streamlit app and go to the tab "View 50 Video Visualization".

### How to run the app

1. Clone the repository
2. Build the docker image: ```docker build tracey:0.0.1 Dockerfile-prod .```
3. Run the docker image and port-forward the Streamlit application: ```docker run -d -p 8501:8501 tracey:0.0.1```

