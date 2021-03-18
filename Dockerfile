FROM python:3.8-slim-buster

WORKDIR /app

# Install backend dependencies necessary to compile SCS and other solvers
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "-m" , "footbot", "serve"]