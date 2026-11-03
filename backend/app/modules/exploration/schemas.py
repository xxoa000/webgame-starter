"""탐색·전투 행동과 보유 회복 아이템 ID를 검증한다."""
from typing import Literal
from pydantic import BaseModel, Field


class StartExploration(BaseModel):
    model_config = {"extra": "forbid"}
    map_id: int = Field(gt=0, strict=True)


class ExplorationAction(BaseModel):
    model_config = {"extra": "forbid"}
    exploration_id: int = Field(gt=0, strict=True)
    action: Literal["search", "rest", "take", "give_up", "end", "fight", "flee", "use_item"]
    version: int = Field(gt=0, strict=True)

    item_id: int | None = Field(default=None, gt=0, strict=True)
