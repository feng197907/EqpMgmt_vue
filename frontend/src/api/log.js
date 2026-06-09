/**
 * Frontend error reporting utilities.
 * Sends JS errors to the backend log endpoint so they are persisted
 * in logs/js_error.log for server-side inspection.
 */

const LOG_ENDPOINT = '/api/v1/log/js-error'

// Deduplicate: avoid spamming the server with identical errors.
const _reported = new Set()

/**
 * Report a JS error to the backend.
 * @param {object} info - Error information
 * @param {string} info.message  - Error message (required)
 * @param {string} [info.source] - Script file URL
 * @param {number} [info.lineno] - Line number
 * @param {number} [info.colno]  - Column number
 * @param {string} [info.stack]  - Full stack trace
 * @param {string} [info.type]   - Error category (e.g. 'unhandledrejection')
 */
export function reportJsError(info) {
  const { message = 'Unknown error', source, lineno, colno, stack, type } = info

  // Deduplicate by message + source:line
  const key = `${message}|${source}:${lineno}`
  if (_reported.has(key)) return
  _reported.add(key)

  const payload = {
    message,
    source: source || null,
    lineno: lineno || null,
    colno: colno || null,
    stack: stack || null,
    page: window.location.pathname,
    user_agent: navigator.userAgent,
    timestamp: new Date().toISOString(),
    extra: type ? { type } : null,
  }

  // Use sendBeacon when available so the report survives page unloads.
  if (navigator.sendBeacon) {
    const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' })
    navigator.sendBeacon(LOG_ENDPOINT, blob)
  } else {
    // Fallback: fire-and-forget fetch (don't await — never block the UI)
    fetch(LOG_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {
      /* swallow network errors silently */
    })
  }
}
