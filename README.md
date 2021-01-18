# footbot

Run
---
    $ python -m footbot
    Usage: __main__.py [OPTIONS] COMMAND [ARGS]...

    Options:
      --debug / --no-debug
      --help                Show this message and exit.
    
    Commands:
      optimise
      serve

Optimise
--------

    $ python -m footbot optimise <team_id> <gameweek>

Serve
-----

    $ python -m footbot serve
     * Serving Flask app "footbot.main" (lazy loading)
     * Environment: production
       WARNING: This is a development server. Do not use it in a production deployment.
       Use a production WSGI server instead.
     * Debug mode: on
    2020-10-06 19:55:20,639 - werkzeug - INFO -  * Running on http://0.0.0.0:8022/ (Press CTRL+C to quit)

Access with credentials
-----------------------

    $ export FPL_LOGIN=my@email.com
    $ export FPL_PASSWORD=mypassword
    $ ./curl.sh "<footbot url>/optimise_team/5002301?start_event=5"

Test
----
    $ python -m pytest

Format
------
    $ ./format.sh
