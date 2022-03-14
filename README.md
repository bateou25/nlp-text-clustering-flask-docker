# NLP-based Text Clustering API using Flask and Docker
This data project demonstrates an end-to-end Natural Language Processing (NLP) project. It clusters a set of texts from an input file and throws the output into a compressed (.zip) Excel file. It is deployed through a REST API using Flask and containerized by using Docker.

### Data
The API uses an [input file](https://drive.google.com/file/d/1HL5hNKcHg1vytkMUUnaJPuXWQDMPN3sf) to perform text clustering.

### Methodology
The web application performs text pre-processing (e.g., removing whitespaces, stemming) and converts the input texts as word embeddings. In particular, it uses a term-document matrix for vectorization. It then performs text clustering using the KMeans library in Python. The application shows the output in a downloadable compressed (.zip) Excel file, with three worksheets: text inputs with associated cluster number, top keywords from each cluster, and the size of each cluster with a corresponding bar chart.

### How to run the Flask app:
1. It is deployed through a Flask app (Apache) and built in a Docker container:
   - Pull from [Docker Hub](www.hub.docker.com)
  ```
  docker pull jaemy29/sample-nlp-text-clustering-flask:1.0.0
  ```
  - Run the docker image
  ```
  docker run -d -p 8000:8000 jaemy29/sample-nlp-text-clustering-flask:1.0.0
  ```
