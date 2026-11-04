import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { authClient } from '../auth'

export default function Login({ user }) {
  const { pathname } = useLocation()
  const isSignUp = pathname === '/signup'
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  if (user) return <Navigate to="/" replace />

  async function handleEmail(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    const fields = new FormData(event.currentTarget)
    try {
      const credentials = { email: fields.get('email').trim(), password: fields.get('password') }
      const result = isSignUp
        ? await authClient.signUp.email({ ...credentials, name: fields.get('name').trim() })
        : await authClient.signIn.email(credentials)
      if (result.error) setError(result.error.message || 'Unable to continue. Please try again.')
      else if (isSignUp && !result.data?.session) setMessage('Account created. Check your email for any verification instructions, then sign in.')
    } catch {
      setError('Unable to connect. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function signInWithGoogle() {
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = await authClient.signIn.social({
        provider: 'google',
        callbackURL: window.location.origin + '/',
      })
      if (result.error) setError(result.error.message || 'Unable to sign in. Please try again.')
    } catch {
      setError('Unable to connect to sign in. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="login-card" aria-labelledby="login-title">
      <div className="login-mark" aria-hidden="true">✦</div>
      <p className="login-eyebrow">TALECRAFT STORY STUDIO</p>
      <h1 id="login-title">{isSignUp ? 'Start your story' : 'Welcome back'}</h1>
      <p className="login-description">{isSignUp ? 'Create an account to begin your next adventure.' : 'Sign in to continue your adventures.'}</p>
      <form className="login-form" onSubmit={handleEmail} key={pathname}>
        {isSignUp && <label htmlFor="name">Name<input id="name" name="name" type="text" autoComplete="name" required /></label>}
        <label htmlFor="email">Email<input id="email" name="email" type="email" autoComplete="email" required /></label>
        <label htmlFor="password">Password<input id="password" name="password" type="password" autoComplete={isSignUp ? 'new-password' : 'current-password'} minLength={isSignUp ? 8 : undefined} required /></label>
        <button className="login-submit" type="submit" disabled={busy}>{busy ? 'Please wait…' : isSignUp ? 'Create account' : 'Sign in'}</button>
      </form>
      <div className="login-divider"><span>or</span></div>
      <button className="google-login" type="button" onClick={signInWithGoogle} disabled={busy}>
        <span className="google-mark" aria-hidden="true">G</span> Continue with Google
      </button>
      {error && <p className="login-error" role="alert">{error}</p>}
      {message && <p className="login-message" role="status">{message}</p>}
      <p className="login-switch">{isSignUp ? 'Already have an account?' : 'New to Talecraft?'}{' '}<Link to={isSignUp ? '/login' : '/signup'} onClick={() => { setError(''); setMessage('') }}>{isSignUp ? 'Sign in' : 'Create an account'}</Link></p>
    </section>
  )
}
