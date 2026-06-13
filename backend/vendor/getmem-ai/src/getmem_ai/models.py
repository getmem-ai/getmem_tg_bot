"""Request and response models for the memory-service public API.

Source of truth: ``plans/memory-service/endpoints.md`` and ``plans/shared/*``.

Response models use ``extra="allow"`` so that fields the server adds in the
future (new ``meta`` timings, extra entity attributes) are preserved rather than
dropped — the SDK never has to be in lock-step with the service to keep working.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["user", "assistant", "system"]


class Message(BaseModel):
    """A single conversation turn passed to :meth:`Client.ingest`."""

    model_config = ConfigDict(extra="forbid")

    role: Role
    content: str
    timestamp: str | None = None  # ISO-8601; server defaults to now if omitted


# ---- responses -------------------------------------------------------------


class _ApiModel(BaseModel):
    """Base for response models: tolerate unknown fields for forward-compat."""

    model_config = ConfigDict(extra="allow")


class IngestResult(_ApiModel):
    status: str
    memories_stored: int = 0
    extraction_queued: bool = False
    request_id: str | None = None


class Memory(_ApiModel):
    id: str
    type: str
    text: str
    category: str | None = None
    relevance_score: float | None = None
    source: str | None = None
    created_at: str | None = None


class ContextMeta(_ApiModel):
    """Timing and diagnostics for a :meth:`Client.get` call.

    Common fields (``total_ms``, ``token_count``, ``memory_count``,
    ``entities_found``) are typed; anything else the server returns is still
    accessible as an attribute thanks to ``extra="allow"``.
    """

    total_ms: int | None = None
    decompose_ms: int | None = None
    search_ms: int | None = None
    graph_ms: int | None = None
    enrich_ms: int | None = None
    rank_ms: int | None = None
    token_count: int | None = None
    memory_count: int | None = None
    entities_found: list[str] = Field(default_factory=list)


class Context(_ApiModel):
    """Assembled context returned by :meth:`Client.get`."""

    context: str = ""
    memories: list[Memory] = Field(default_factory=list)
    meta: ContextMeta = Field(default_factory=ContextMeta)


class DeleteResult(_ApiModel):
    status: str
    memories_deleted: int = 0
    entities_deleted: int = 0
    relations_deleted: int = 0


class ListMemoriesResult(_ApiModel):
    memories: list[Memory] = Field(default_factory=list)
    total: int = 0
    limit: int = 0
    offset: int = 0


class Relation(_ApiModel):
    target: str
    type: str
    weight: float | None = None
    context: str | None = None


class Entity(_ApiModel):
    id: str
    name: str
    type: str | None = None
    tags: list[str] = Field(default_factory=list)
    mention_count: int | None = None
    decay_score: float | None = None
    relations: list[Relation] = Field(default_factory=list)


class ListEntitiesResult(_ApiModel):
    entities: list[Entity] = Field(default_factory=list)
    total: int = 0


class HealthStatus(_ApiModel):
    status: str
    details: dict[str, Any] | None = None
