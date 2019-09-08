from sanic import Sanic
from sanic.response import json, text
import time

app = Sanic()


@app.route('/')
async def test(_):
    return text('Greetings!')


@app.get('/status')
async def status(_):
    return json({'OK': time.time(), 'status': 200})


def run():
    app.run(host="0.0.0.0", port=7754)