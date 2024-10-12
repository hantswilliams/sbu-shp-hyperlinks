FROM python:3.11.6-alpine3.18
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
EXPOSE 5009
CMD [ "python", "app.py" ]

# build command: docker build -t linkchecker .
# run command: docker run -p 5009:5009 linkchecker