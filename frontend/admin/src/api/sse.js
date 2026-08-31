// SSE 클라이언트 (Q9=A).
// 브라우저 EventSource 는 Authorization 헤더를 지원하지 않으므로
// fetch + ReadableStream 으로 직접 구현해 Bearer 헤더를 전송한다.
// 재연결 시 Last-Event-ID 헤더로 마지막 수신 ID 를 전달한다(§2.1).

export function openOrderStream({ onEvent, onOpen, onError, getLastEventId }) {
  const controller = new AbortController()
  let closed = false

  async function connect() {
    const token = localStorage.getItem('admin_token')
    const headers = {
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
    const lastId = getLastEventId?.()
    if (lastId != null) headers['Last-Event-ID'] = String(lastId)

    try {
      const res = await fetch('/api/admin/orders/stream', {
        headers,
        signal: controller.signal,
      })
      if (!res.ok || !res.body) throw new Error(`SSE HTTP ${res.status}`)
      onOpen?.()

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (!closed) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        // 프레임은 빈 줄(\n\n)로 구분(§2.2)
        let sep
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const raw = buffer.slice(0, sep)
          buffer = buffer.slice(sep + 2)
          const frame = parseFrame(raw)
          if (frame) onEvent?.(frame)
        }
      }
    } catch (err) {
      if (!closed) onError?.(err)
    }
  }

  function parseFrame(raw) {
    const out = { id: null, event: 'message', data: null }
    for (const line of raw.split('\n')) {
      if (line.startsWith('id:')) out.id = Number(line.slice(3).trim())
      else if (line.startsWith('event:')) out.event = line.slice(6).trim()
      else if (line.startsWith('data:')) {
        const payload = line.slice(5).trim()
        try { out.data = JSON.parse(payload) } catch (_) { out.data = payload }
      }
    }
    return out.data !== null || out.id !== null ? out : null
  }

  connect()

  return {
    close() { closed = true; controller.abort() },
  }
}
