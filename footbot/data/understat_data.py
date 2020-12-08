import asyncio
import aiohttp
from understat import Understat


async def get_league_players_async(season):
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        players = await us.get_league_players(
            "epl",
            season
        )

    return players


def get_league_players(season):
    return asyncio.run(get_league_players_async(season))


async def get_teams_async(season):
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        players = await us.get_teams(
            "epl",
            season
        )

    return players


def get_teams(season):
    return asyncio.run(get_teams_async(season))


async def get_league_results_async(season):
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        players = await us.get_league_results(
            "epl",
            season
        )

    return players


def get_league_results(season):
    return asyncio.run(get_league_results_async(season))


async def get_match_players_async(fixture_id):
    async with aiohttp.ClientSession() as session:
        us = Understat(session)
        players = await us.get_match_players(
            fixture_id
        )

    return players


def get_match_players(fixture_id):
    return asyncio.run(get_match_players_async(fixture_id))
