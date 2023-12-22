from typing import TypedDict


class TeamDict(TypedDict):
    id: int
    name: str


class TournamentDict(TypedDict):
    id: int
    name: str
    years: str