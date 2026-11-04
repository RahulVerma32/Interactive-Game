// Neon injects the signed JWT into the session response's token field.
function tokenIsFresh(token, now = Date.now()) {
  if (typeof token !== 'string') return false
  try {
    const payload = token.split('.')[1]
    if (!payload) return false
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const { exp } = JSON.parse(json)
    return typeof exp === 'number' && exp * 1000 > now + 30_000
  } catch {
    return false
  }
}

export async function getSessionToken(client) {
  let result
  try {
    result = await client.getSession()
    if (!result.error && tokenIsFresh(result.data?.session?.token)) {
      return result.data.session.token
    }
    // Bypass the SDK's cached session when its JWT is missing or near expiry.
    result = await client.getSession({ fetchOptions: { headers: { 'X-Force-Fetch': 'true' } } })
  } catch {
    throw new Error('Unable to verify your session. Check your connection and try again.')
  }
  if (result.error) {
    throw new Error('Unable to verify your session. Check your connection and try again.')
  }
  if (!result.data?.user || !result.data?.session) {
    throw new Error('Your session has expired. Please sign in again.')
  }
  if (!tokenIsFresh(result.data.session.token)) {
    throw new Error('Unable to retrieve a valid session token. Please sign out and sign in again.')
  }
  return result.data.session.token
}
