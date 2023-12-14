from typing import ClassVar, Literal, List

from pydantic import BaseModel
from database import get_db


db = get_db()


class BaseModelDB(BaseModel):
    table_name: ClassVar = ""
    pk: str = "id"

    def model_dump(self, *, exclude=None, **_):
        to_exclude = set([*(exclude or []), "table_name"])
        model = super().model_dump(by_alias=True, exclude=to_exclude, exclude_none=True)
        return model

    def save(self):
        return db.insert_dict(self.table_name, self.model_dump(exclude=["pk"]), self.pk)

    def update(self):
        data = self.model_dump()
        pk = data.pop(self.pk)
        db.update(self.table_name, data, {self.pk: pk})

    @classmethod
    def get(cls, key: str):
        result = db.select(cls.table_name, {cls.pk: key})
        assert len(result) == 1, "More than one result found"
        return cls(**result[0])


Role = Literal["creator", "consumer"]


class Url(BaseModelDB):
    """Models a user."""

    table_name: ClassVar = "urls"
    pk: ClassVar = "id"

    id: int = None
    url: str = None
    label: str = None
    access_count: int = 0

    @classmethod
    def from_url_create(cls, url_create: "UrlCreate"):
        return cls(**url_create.model_dump())

    @classmethod
    def get_top_urls(cls):
        results = db.select_raw(
            f"""
            SELECT * FROM "{cls.table_name}" ORDER BY access_count DESC LIMIT 100
        """
        )

        return [cls(**result) for result in results]


class UrlCreate(BaseModel):
    url: str
