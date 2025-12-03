import { useState, useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import axios from "axios"
import { API_BASE_URL } from "../util.js"
import "./StorySidebar.css"

function StorySidebar() {
    const navigate = useNavigate()
    const location = useLocation()
    const [stories, setStories] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchStories()
    }, [])

    const fetchStories = async () => {
        try {
            setLoading(true)
            const response = await axios.get(`${API_BASE_URL}/stories`)
            setStories(response.data)
            setError(null)
        } catch (e) {
            setError(`Failed to load stories: ${e.message}`)
        } finally {
            setLoading(false)
        }
    }

    const handleStoryClick = (storyId) => {
        navigate(`/story/${storyId}`)
    }

    const handleNewStory = () => {
        navigate("/")
    }

    const formatDate = (dateString) => {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: 'numeric'
        })
    }

    const isActiveStory = (storyId) => {
        return location.pathname === `/story/${storyId}`
    }

    return (
        <div className="story-sidebar">
            <div className="sidebar-header">
                <h2>My Stories</h2>
                <button className="new-story-btn" onClick={handleNewStory}>
                    + New Story
                </button>
            </div>

            <div className="sidebar-content">
                {loading && <div className="sidebar-loading">Loading stories...</div>}
                
                {error && <div className="sidebar-error">{error}</div>}
                
                {!loading && !error && stories.length === 0 && (
                    <div className="no-stories">
                        <p>No stories yet.</p>
                        <p>Create your first adventure!</p>
                    </div>
                )}

                {!loading && !error && stories.length > 0 && (
                    <div className="story-list">
                        {stories.map((story) => (
                            <div
                                key={story.id}
                                className={`story-item ${isActiveStory(story.id) ? 'active' : ''}`}
                                onClick={() => handleStoryClick(story.id)}
                            >
                                <div className="story-title">{story.title}</div>
                                <div className="story-meta">
                                    {story.theme && <span className="story-theme">{story.theme}</span>}
                                    <span className="story-date">{formatDate(story.created_at)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default StorySidebar
