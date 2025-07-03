import json

import pydantic
from pydantic import BaseModel

from bot.config import settings
from bot.services import http


class Clock(BaseModel):
    increment: int
    limit: int


class Tournament(BaseModel):
    id: str
    status: str
    clock: Clock


class LichessAPI:
    def __init__(self, token: str, team_id: str):
        self.headers = {"Authorization": f"Bearer {token}"}
        self.team = team_id

    async def get_team_tournament(self) -> Tournament:
        async with http.session.get(
            f"https://lichess.org/api/team/{self.team}/swiss",
            headers=self.headers,
            params={"max": 1},
            raise_for_status=True,
        ) as resp:
            try:
                return Tournament.parse_obj(await resp.json(content_type="application/x-ndjson"))
            except pydantic.error_wrappers.ValidationError:
                return Tournament(id="0", status="finished", clock={"limit": 60, "increment": 0})

    async def get_tournament(self, tournament_id: str) -> Tournament:
        async with http.session.get(
            f"https://lichess.org/api/swiss/{tournament_id}",
            headers=self.headers,
            raise_for_status=True,
        ) as resp:
            return Tournament.parse_obj(await resp.json())

    async def get_tournament_results(self, tournament_id: str) -> list[dict]:
        async with http.session.get(
            f"https://lichess.org/api/swiss/{tournament_id}/results",
            headers=self.headers,
            params={"nb": 3},
            raise_for_status=True,
        ) as resp:
            results = await resp.text()
            return [json.loads(result) for result in results.split("\n") if result]

    async def create_tournament(
        self, name: str, start_time: int, increment: int, limit: int, rounds: int
    ) -> Tournament:
        async with http.session.post(
            f"https://lichess.org/api/swiss/new/{self.team}",
            headers=self.headers,
            data={
                "name": name,
                "clock.limit": limit,
                "clock.increment": increment,
                "nbRounds": rounds,
                "startsAt": start_time,
            },
            raise_for_status=True,
        ) as resp:
            return Tournament.parse_obj(await resp.json())


lichess = LichessAPI(settings.chess.access_token, settings.chess.team_id)
