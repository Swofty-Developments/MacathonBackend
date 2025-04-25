from typing import override, Self
from pydantic import BaseModel

__all__ = [ "DBRecord" ]


class DBRecord(BaseModel):
    id: int

    def model_dump_safe(self, *args, **kwargs) -> dict:
        kwargs["exclude"] = kwargs.get("exclude", []) + ["id"]

        dump = super().model_dump(*args, **kwargs)

        return dump

    @override
    def model_dump(self, *args, **kwargs) -> dict:
        kwargs["exclude"] = kwargs.get("exclude", []) + ["id"]

        dump = super().model_dump(*args, **kwargs)
        dump["_id"] = self.id

        return dump

    @override
    def model_dump_json(self, *args, **kwargs) -> str:
        kwargs["exclude"] = kwargs.get("exclude", []) + ["id"]

        dump = super().model_dump_json(*args, **kwargs)
        dump["_id"] = self.id

        return dump

    @override
    @classmethod
    def model_validate(cls, *args, **kwargs) -> Self:
        kwargs["obj"] = args[0] if len(args) > 0 else kwargs.get("obj", {})

        if kwargs["obj"]:
            kwargs["obj"]["id"] = kwargs["obj"].pop("_id")

        return super().model_validate(**kwargs)
