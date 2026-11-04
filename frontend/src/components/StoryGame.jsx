import { useState } from 'react'
import api from '../api'
import { API_BASE_URL } from '../util'
import { shuffleOptions } from './optionShuffle.mjs'

function formatChapterHeading(number, title) {
  const cleaned = (title || '').replace(/^\s*chapter\s+\d+\s*(?:[:.\-–—]\s*|$)/i, '').trim()
  return cleaned ? `Chapter ${number}: ${cleaned}` : `Chapter ${number}`
}
function StoryGame({ story, onNewStory, onReload }) {
  const [version, setVersion] = useState(story.progress_version || 0)
  const [hearts, setHearts] = useState(story.hearts ?? 3)
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [selectedOption, setSelectedOption] = useState(null)
  const [visited, setVisited] = useState(() => [story.current_node_id || story.root_node.id])
  const [viewIndex, setViewIndex] = useState(0)
  const currentNodeId = visited[visited.length - 1]
  const viewingPast = viewIndex < visited.length - 1
  const currentNode = story.all_nodes[visited[viewIndex]]
  const [displayedOptions, setDisplayedOptions] = useState(() =>
    shuffleOptions(story.all_nodes[story.current_node_id || story.root_node.id]?.options)
  )

  async function saveProgress(action, payload) {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const { data } = await api.post(`${API_BASE_URL}/stories/${story.id}/${action}`, { ...payload, version })
      setSelectedOption(null)
      if (!story.all_nodes[data.current_node_id]) {
        await onReload()
        return
      }
      setDisplayedOptions(shuffleOptions(story.all_nodes[data.current_node_id].options))
      setVersion(data.version)
      setHearts(data.hearts)
      if (action !== 'choice' || data.reset_to_checkpoint) {
        setVisited([data.current_node_id])
        setViewIndex(0)
      } else if (data.current_node_id !== currentNodeId) {
        setVisited(previous => [...previous, data.current_node_id])
        setViewIndex(previous => previous + 1)
      }
      if (data.reset_to_checkpoint) setNotice('You ran out of hearts. Start again from the beginning of this chapter.')
      else if (data.wrong) setNotice('That choice cost you a heart. Try another option.')
    } catch (err) {
      setError(err.response?.status === 409 ? 'Your progress changed in another session. Reload to continue.' : 'Could not save your progress. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  if (!currentNode) return <div className="error-message">This story could not be loaded.</div>

  return <div className="story-game">
    <header className="story-header">
      <div className="story-header-actions"><button type="button" className="replay-btn" onClick={() => saveProgress('restart', {})} disabled={busy} title="Restart the entire story and restore your hearts. The story remains saved." aria-label="Replay: restart the entire story and restore your hearts; the story remains saved">↻ Replay</button></div>
      <h2>{story.title}</h2>
      <div className="hearts" role="status" aria-label={`${hearts} of 3 hearts remaining`}><span aria-hidden="true">{Array.from({ length: 3 }, (_, index) => <span key={index} className={index < hearts ? 'heart-full' : 'heart-empty'}>♥</span>)}</span></div>
      {currentNode.chapter_number && <p>{formatChapterHeading(currentNode.chapter_number, currentNode.chapter_title)}</p>}
    </header>
    <div className="story-content">
      <div className="story-node">
        <p>{currentNode.content}</p>
        {currentNode.is_ending ? <div className="story-ending"><h3>{currentNode.is_winning_ending ? 'Congratulations' : 'The End'}</h3><p>Your adventure has ended.</p></div> :
          <div className="story-options"><h3>What will you do?</h3><div className="options-list">
            {(viewingPast ? currentNode.options : displayedOptions).map((option) => <button key={option.id || option.number} type="button" onClick={() => { setSelectedOption(option.number); setNotice('') }} className={`option-btn${!viewingPast && selectedOption === option.number ? ' selected' : ''}`} aria-pressed={!viewingPast && selectedOption === option.number} disabled={busy || viewingPast}>{option.text}</button>)}
          </div></div>}
      </div>
      {viewingPast && <p className="history-notice" role="status">Reviewing an earlier scene. Return to your current scene to make a choice.</p>}
      {notice && <p className="heart-notice" role="status">{notice}</p>}
      {error && <div className="error-message" role="alert"><p>{error}</p><button type="button" onClick={onReload}>Reload story</button></div>}
      <div className="story-controls">
        <div className="scene-navigation">
          <button type="button" className="previous-btn" disabled={busy || viewIndex === 0} onClick={() => { setSelectedOption(null); setViewIndex(index => index - 1) }}>← Previous</button>
          <button type="button" className="next-btn" disabled={busy || (!viewingPast && (currentNode.is_ending || selectedOption === null))} onClick={() => viewingPast ? setViewIndex(index => index + 1) : saveProgress('choice', { node_id: currentNodeId, option_number: selectedOption })} title={viewingPast ? 'Go forward to a scene you have visited' : 'Select an option and press Next to continue'}>Next →</button>
        </div>
      </div>
      {onNewStory && <button type="button" onClick={onNewStory} className="new-story-btn">New Story</button>}
    </div>
  </div>
}

export default StoryGame
