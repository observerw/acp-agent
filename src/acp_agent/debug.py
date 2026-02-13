from __future__ import annotations

from datetime import UTC, datetime
from random import Random
from typing import Any
from uuid import uuid4

from acp.core import run_agent
from acp.helpers import update_agent_message_text
from acp.interfaces import Agent, Client
from acp.schema import (
    AgentCapabilities,
    AudioContentBlock,
    AuthenticateResponse,
    ClientCapabilities,
    EmbeddedResourceContentBlock,
    ForkSessionResponse,
    HttpMcpServer,
    ImageContentBlock,
    Implementation,
    InitializeResponse,
    ListSessionsResponse,
    LoadSessionResponse,
    McpServerStdio,
    ModelInfo,
    NewSessionResponse,
    PromptCapabilities,
    PromptResponse,
    ResourceContentBlock,
    ResumeSessionResponse,
    SessionCapabilities,
    SessionForkCapabilities,
    SessionInfo,
    SessionListCapabilities,
    SessionMode,
    SessionModelState,
    SessionModeState,
    SessionResumeCapabilities,
    SetSessionModelResponse,
    SetSessionModeResponse,
    SseMcpServer,
    TextContentBlock,
)
from attrs import define, field

type PromptBlock = (
    TextContentBlock
    | ImageContentBlock
    | AudioContentBlock
    | ResourceContentBlock
    | EmbeddedResourceContentBlock
)
type McpServer = HttpMcpServer | SseMcpServer | McpServerStdio

MODEL_ID = "dummy-random"
MODE_ID = "default"
WORDS = (
    "amber",
    "brisk",
    "cinder",
    "delta",
    "ember",
    "fable",
    "glimmer",
    "harbor",
    "ion",
    "jolt",
    "kernel",
    "lattice",
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@define
class _SessionState:
    cwd: str
    mode_id: str = MODE_ID
    model_id: str = MODEL_ID
    updated_at: str = field(factory=_now_iso)


@define
class DummyAgent(Agent):
    seed: int | None = None
    _client: Client | None = field(default=None, init=False)
    _rng: Random = field(init=False)
    _sessions: dict[str, _SessionState] = field(factory=dict, init=False)

    def __attrs_post_init__(self) -> None:
        self._rng = Random(self.seed)

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: ClientCapabilities | None = None,
        client_info: Implementation | None = None,
        **kwargs: object,
    ) -> InitializeResponse:
        _ = client_capabilities, client_info, kwargs
        return InitializeResponse(
            protocol_version=protocol_version,
            agent_info=Implementation(name="acp-agent-dummy", version="0.1.0"),
            agent_capabilities=AgentCapabilities(
                load_session=True,
                prompt_capabilities=PromptCapabilities(),
                session_capabilities=SessionCapabilities(
                    list=SessionListCapabilities(),
                    fork=SessionForkCapabilities(),
                    resume=SessionResumeCapabilities(),
                ),
            ),
        )

    async def new_session(
        self,
        cwd: str,
        mcp_servers: list[McpServer],
        **kwargs: object,
    ) -> NewSessionResponse:
        _ = mcp_servers, kwargs
        session_id = str(uuid4())
        self._sessions[session_id] = _SessionState(cwd=cwd)
        state = self._sessions[session_id]
        return NewSessionResponse(
            session_id=session_id,
            models=self._models(state.model_id),
            modes=self._modes(state.mode_id),
        )

    async def load_session(
        self,
        cwd: str,
        mcp_servers: list[McpServer],
        session_id: str,
        **kwargs: object,
    ) -> LoadSessionResponse | None:
        _ = mcp_servers, kwargs
        session = self._sessions.get(session_id)
        if session is None:
            return None

        session.cwd = cwd
        session.updated_at = _now_iso()
        return LoadSessionResponse(
            models=self._models(session.model_id),
            modes=self._modes(session.mode_id),
        )

    async def list_sessions(
        self,
        cursor: str | None = None,
        cwd: str | None = None,
        **kwargs: object,
    ) -> ListSessionsResponse:
        _ = cursor, kwargs
        sessions = [
            SessionInfo(
                session_id=session_id,
                cwd=session.cwd,
                title=f"Dummy {session_id[:8]}",
                updated_at=session.updated_at,
            )
            for session_id, session in self._sessions.items()
            if cwd is None or session.cwd == cwd
        ]
        return ListSessionsResponse(sessions=sessions)

    async def set_session_mode(
        self,
        mode_id: str,
        session_id: str,
        **kwargs: object,
    ) -> SetSessionModeResponse | None:
        _ = kwargs
        session = self._sessions.get(session_id)
        if session is None:
            return None

        session.mode_id = mode_id
        session.updated_at = _now_iso()
        return SetSessionModeResponse()

    async def set_session_model(
        self,
        model_id: str,
        session_id: str,
        **kwargs: object,
    ) -> SetSessionModelResponse | None:
        _ = kwargs
        session = self._sessions.get(session_id)
        if session is None:
            return None

        session.model_id = model_id
        session.updated_at = _now_iso()
        return SetSessionModelResponse()

    async def authenticate(
        self,
        method_id: str,
        **kwargs: object,
    ) -> AuthenticateResponse | None:
        _ = method_id, kwargs
        return AuthenticateResponse()

    async def prompt(
        self,
        prompt: list[PromptBlock],
        session_id: str,
        **kwargs: object,
    ) -> PromptResponse:
        _ = prompt, kwargs
        session = self._sessions.setdefault(session_id, _SessionState(cwd="."))
        session.updated_at = _now_iso()

        if self._client:
            await self._client.session_update(
                session_id=session_id,
                update=update_agent_message_text(self._random_text()),
            )

        return PromptResponse(stop_reason="end_turn")

    async def fork_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[McpServer] | None = None,
        **kwargs: object,
    ) -> ForkSessionResponse:
        _ = mcp_servers, kwargs
        source = self._sessions.get(session_id, _SessionState(cwd=cwd))
        new_session_id = str(uuid4())
        self._sessions[new_session_id] = _SessionState(
            cwd=cwd,
            mode_id=source.mode_id,
            model_id=source.model_id,
        )
        state = self._sessions[new_session_id]
        return ForkSessionResponse(
            session_id=new_session_id,
            models=self._models(state.model_id),
            modes=self._modes(state.mode_id),
        )

    async def resume_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[McpServer] | None = None,
        **kwargs: object,
    ) -> ResumeSessionResponse:
        _ = mcp_servers, kwargs
        state = self._sessions.setdefault(session_id, _SessionState(cwd=cwd))
        state.cwd = cwd
        state.updated_at = _now_iso()
        return ResumeSessionResponse(
            models=self._models(state.model_id),
            modes=self._modes(state.mode_id),
        )

    async def cancel(self, session_id: str, **kwargs: object) -> None:
        _ = session_id, kwargs

    async def ext_method(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "method": method,
            "params": params,
            "ok": True,
        }

    async def ext_notification(self, method: str, params: dict[str, Any]) -> None:
        _ = method, params

    def on_connect(self, conn: Client) -> None:
        self._client = conn

    def _modes(self, current_mode_id: str) -> SessionModeState:
        return SessionModeState(
            current_mode_id=current_mode_id,
            available_modes=[
                SessionMode(
                    id=MODE_ID,
                    name="Default",
                )
            ],
        )

    def _models(self, current_model_id: str) -> SessionModelState:
        return SessionModelState(
            current_model_id=current_model_id,
            available_models=[
                ModelInfo(
                    model_id=MODEL_ID,
                    name="Dummy Random",
                )
            ],
        )

    def _random_text(self) -> str:
        size = self._rng.randint(4, 8)
        tokens = [self._rng.choice(WORDS) for _ in range(size)]
        sentence = " ".join(tokens)
        return f"dummy: {sentence}."

    @classmethod
    async def run(cls, *, seed: int | None = None) -> None:
        await run_agent(cls(seed=seed))
