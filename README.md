# footbot

We run footbot using Docker. If you don't already have Docker on your machine, you can install Docker Desktop here:  
https://www.docker.com/get-started

Optimise
--------

    $ docker-compose run --rm footbot python -m footbot optimise <team_id> <gameweek>

Serve
-----

    $ make serve
     make clean-container
     docker rm -f footbot
     footbot
     docker-compose run --service-ports --name footbot footbot
     Creating footbot_footbot_run ... done
      * Serving Flask app "footbot.main" (lazy loading)
      * Environment: production
        WARNING: This is a development server. Do not use it in a production deployment.
        Use a production WSGI server instead.
      * Debug mode: on
     2021-03-17 16:33:28,066 - werkzeug - INFO -  * Running on http://0.0.0.0:8022/ (Press CTRL+C to quit)



Access with credentials
-----------------------

    $ export FPL_LOGIN=<email>
    $ export FPL_PASSWORD=<password>
    $ ./curl.sh "<footbot url>/optimise_team/<team_id>?start_event=<gameweek>"

Test
----
    $ make test

Format
------
    $ make format
