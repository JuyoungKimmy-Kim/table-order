"""Unit 1: SSE 이벤트 브로커 (Integration Contract §2).

인메모리 비동기 pub/sub. 소규모 단일 프로세스 가정.
- publish(event, payload): 모든 구독자에게 이벤트 전달(이벤트 id 단조 증가).
- subscribe(): async generator, SSE 프레임 문자열을 yield.
- format_sse(id, event, data): 프레임 직렬화.

발행 유닛(2/4/3)은 publish() 만 호출한다. 구독(Unit 3)은 subscribe() 로
StreamingResponse(media_type="text/event-stream") 를 만든다.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator


class SSEBroker:
    def __init__(self, max_recent: int = 100) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._seq: int = 0
        self._recent: list[dict[str, Any]] = []
        self._max_recent = max_recent
        self._lock = asyncio.Lock()

    async def publish(self, event: str, payload: Any) -> int:
        """이벤트를 모든 구독자 큐에 넣는다. 부여된 이벤트 id 반환."""
        async with self._lock:
            self._seq += 1
            frame = {"id": self._seq, "event": event, "data": payload}
            self._recent.append(frame)
            if len(self._recent) > self._max_recent:
                self._recent.pop(0)
            subscribers = list(self._subscribers)
        for q in subscribers:
            q.put_nowait(frame)
        return self._seq

    async def subscribe(self, last_event_id: int | None = None) -> AsyncIterator[str]:
        """구독 async generator. Last-Event-ID 이후 이벤트를 best-effort 재전송."""
        q: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(q)
            backlog = [f for f in self._recent if last_event_id is None or f["id"] > last_event_id]
        try:
            for frame in backlog:
                yield format_sse(frame["id"], frame["event"], frame["data"])
            while True:
                frame = await q.get()
                yield format_sse(frame["id"], frame["event"], frame["data"])
        finally:
            async with self._lock:
                self._subscribers.discard(q)


def format_sse(event_id: int, event: str, data: Any) -> str:
    """SSE 프레임 직렬화 (§2.2)."""
    body = json.dumps(data, ensure_ascii=False)
    return f"id: {event_id}\nevent: {event}\ndata: {body}\n\n"


# 프로세스 전역 브로커 인스턴스 (단일 프로세스 가정).
broker = SSEBroker()


async def publish(event: str, payload: Any) -> int:
    """전역 브로커 publish 편의 함수 — 각 유닛이 이것을 호출한다."""
    return await broker.publish(event, payload)


def subscribe(last_event_id: int | None = None) -> AsyncIterator[str]:
    """전역 브로커 subscribe 편의 함수 (Unit 3 소비)."""
    return broker.subscribe(last_event_id)
