import './App.css'
import { useEffect, useState } from 'react'
import {BrowserRouter as Router, Routes, Route, Link, Navigate} from "react-router-dom"
import StoryLoader from "./components/StoryLoader"
import StoryGenerator from "./components/StoryGenerator.jsx";
import Login from './components/Login.jsx'
import { authClient } from './auth'

function App() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('talecraft-theme') || 'light' } catch { return 'light' }
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('talecraft-theme', theme) } catch { /* Preference remains active for this session. */ }
  }, [theme])
  const { data: session, isPending } = authClient.useSession()
  const user = session?.user
  return (
    <Router>
      <div className="app-container">
        <header className="site-header">
          <Link className="brand" to="/"><span className="brand-icon">✦</span><span>tale<span className="brand-accent">craft</span><small>STORY STUDIO</small></span></Link>
          <nav className="account-nav" aria-label="Account">
            <button className="theme-toggle" type="button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`} title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>{theme === 'light' ? '☾' : '☀'}</button>
            {isPending ? <span>Checking session…</span> : user ? (
              <><span className="user-avatar">{(user.name || user.email || 'U').charAt(0).toUpperCase()}</span><span className="user-name">{user.name || user.email}</span><button type="button" onClick={() => authClient.signOut()}>Sign out</button></>
            ) : <><Link to="/login">Sign in</Link><Link className="account-signup" to="/signup">Create account</Link></>}
          </nav>
        </header>
        <main>
          <Routes>
            <Route path={"/story/:id"} element={isPending ? <p>Checking session…</p> : user ? <StoryLoader /> : <Navigate to="/login" replace />} />
            <Route path={"/"} element={isPending ? <p>Checking session…</p> : user ? <StoryGenerator user={user} /> : <Navigate to="/login" replace />}/>
            <Route path="/login" element={isPending ? <p>Checking session…</p> : <Login user={user} />} />
            <Route path="/signup" element={isPending ? <p>Checking session…</p> : <Login user={user} />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

