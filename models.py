import datetime
from dataclasses import dataclass
from typing import TypeVar, Generic

from fastapi import UploadFile
from pydantic import BaseModel, HttpUrl

T = TypeVar('T')


@dataclass
class Release:
    name: str
    version: str
    date: datetime.datetime
    assets: list[HttpUrl]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "date": self.date,
            "assets": self.assets
        }


@dataclass
class CreateReleaseDto:
    name: str
    version: str
    files: list[UploadFile]

    def to_release(self, urls: list[HttpUrl]) -> Release:
        return Release(
            name=self.name,
            version=self.version,
            date=datetime.datetime.now(),
            assets=urls
        )


@dataclass
class Pagination(Generic[T]):
    page: int
    per: int
    total: int
    total_pages: int
    items: list[T]
