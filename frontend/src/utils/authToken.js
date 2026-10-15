const STORAGE_KEY = 'ecovision_token'

export function getToken() {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(STORAGE_KEY, token)
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Storage unavailable: the user stays logged out after reload.
  }
}

/** Fired when the server rejects the stored token (e.g. logged out elsewhere). */
export const TOKEN_REJECTED_EVENT = 'ecovision:token-rejected'
