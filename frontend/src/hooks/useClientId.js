const STORAGE_KEY = 'ecovision_client_id'

let cachedId = null

function generateUuid() {
  // crypto.randomUUID exists only in secure contexts (https / localhost),
  // so fall back to getRandomValues when the app is opened by LAN IP.
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/** Anonymous device ID: generated once and kept in localStorage. */
export function getClientId() {
  if (cachedId) return cachedId
  try {
    cachedId = localStorage.getItem(STORAGE_KEY)
  } catch {
    // Storage may be unavailable (private mode); the ID then lives for this session only.
  }
  if (!cachedId) {
    cachedId = generateUuid()
    try {
      localStorage.setItem(STORAGE_KEY, cachedId)
    } catch {
      // ignore
    }
  }
  return cachedId
}

export default function useClientId() {
  return getClientId()
}
