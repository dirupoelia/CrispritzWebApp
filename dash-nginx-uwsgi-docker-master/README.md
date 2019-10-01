# Dash - nginx - uWSGI - Docker

Dash by Plotly is a Python framework to build elegant interactive dashboards for the web. This template can be used to create a Docker image that uses Flask, Nginx, and uWSGI to serve the application.

## Dockerize your Dash app

1. Create Docker image
```
docker build -t my_dashboard .
```

2. Run app in container
```
docker run -p 8080:80 my_dashboard
```
This will run the app on http://localhost:8080/.

The base image used in the Dockerfile: https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/. 

## When changing the app:

Change the ip from 127.0.0.1:8050 to 1577.27.31.58, and possibly the name to app.py
Note that the installed crispritz does not generate .png images from .pdf, so add after the if generate_report:
```
for i in *.pdf; do
   pdftoppm -png -rx 300 -ry 300 $i ${i%.pdf*}
done
rename 's/-1//g' ./*
```

And the last line to
```
app.run_server(host='0.0.0.0', debug=True, port=80)
```

To run use
```
docker run -p 8080:80 my_dashboard python3 app.py
```
