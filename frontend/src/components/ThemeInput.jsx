import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import { API_BASE_URL } from '../util'

function ThemeInput({ onSubmit, user }) {
  const [theme, setTheme] = useState('')
  const [error, setError] = useState('')
  const [history, setHistory] = useState(null)
  const [historyError, setHistoryError] = useState(false)
  const firstName = (user?.name || user?.email?.split('@')[0] || 'there').trim().split(/\s+/)[0]

  useEffect(() => {
    let active = true
    api.get(`${API_BASE_URL}/stories`).then(({ data }) => {
      if (active) setHistory(data)
    }).catch(() => {
      if (active) setHistoryError(true)
    })
    return () => { active = false }
  }, [user?.id])

  function handleSubmit(event) {
    event.preventDefault()
    if (!theme.trim()) {
      setError('Enter a story idea to begin.')
      return
    }
    onSubmit(theme.trim())
  }

  return (
    <div className="home-layout">
      <aside className="history-sidebar" aria-labelledby="history-title">
        <div className="history-heading"><h2 id="history-title">History</h2><span aria-hidden="true">↗</span></div>
        {historyError ? <p className="history-empty">Could not load your stories.</p> : history === null ? <p className="history-empty">Loading stories…</p> : history.length === 0 ? <p className="history-empty">Your stories will appear here.</p> : (
          <nav className="history-list" aria-label="Story history">
            {history.map((story) => <Link className="history-item" key={story.id} to={`/story/${story.id}`}><span className="history-item-icon" aria-hidden="true">✧</span><span>{story.title}</span></Link>)}
          </nav>
        )}
      </aside>
      <section className="home-main" aria-labelledby="welcome-title">
        <div className="welcome-content">
          <div className="welcome-icon" aria-hidden="true">✦</div>
          <h1 id="welcome-title">Welcome, {firstName}</h1>
          <p>Ready to adventure?</p>
          <form className="story-search" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="story-theme">Your story idea</label>
            <span className="search-icon" aria-hidden="true">⌕</span>
            <input id="story-theme" value={theme} onChange={(event) => { setTheme(event.target.value); setError('') }} placeholder="Where will your story take you?" aria-invalid={Boolean(error)} aria-describedby={error ? 'theme-error' : undefined} />
            <button type="submit" aria-label="Create story">→</button>
          </form>
          {error && <p className="search-error" id="theme-error" role="alert">{error}</p>}
          <span className="search-hint">Enter an idea to begin</span>
        </div>
      </section>
    </div>
  )
}

export default ThemeInput
