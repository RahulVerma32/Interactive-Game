import {useState, useEffect, useCallback} from "react"
import {useNavigate} from "react-router-dom";
import axios from "../api.js";
import ThemeInput from "./ThemeInput.jsx";
import LoadingStatus from "./LoadingStatus.jsx";
import {API_BASE_URL} from "../util.js";


function StoryGenerator({user}) {
    const navigate = useNavigate()
    const [theme, setTheme] = useState("")
    const [jobId, setJobId] = useState(null)
    const [jobStatus, setJobStatus] = useState(null)
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)

    const pollJobStatus = useCallback(async (id) => {
        try {
            const response = await axios.get(`${API_BASE_URL}/jobs/${id}`, {withCredentials: true})
            const {status, story_id, error: jobError} = response.data
            setJobStatus(status)

            if (status === "completed" && story_id) {
                setLoading(false)
                navigate(`/story/${story_id}`)
            } else if (status === "completed") {
                setJobStatus("failed")
                setError("Story generation completed without a story. Please try again.")
                setLoading(false)
            } else if (status === "failed" || jobError) {
                setError(jobError || "Failed to generate story")
                setLoading(false)
            }
        } catch (e) {
            setJobStatus("failed")
            setError(`Failed to check story status: ${e.message}`)
            setLoading(false)
        }
    }, [navigate])

    useEffect(() => {
        let pollInterval;

        if (jobId && (jobStatus === "pending" || jobStatus === "processing")) {
            pollInterval = setInterval(() => {
                pollJobStatus(jobId)
            }, 5000)
        }

        return () => {
            if (pollInterval) {
                clearInterval(pollInterval)
            }
        }
    }, [jobId, jobStatus, pollJobStatus])

    const generateStory = async (theme) => {
        setLoading(true)
        setError(null)
        setTheme(theme)

        try {
            const response = await axios.post(`${API_BASE_URL}/stories/create`, {theme}, {withCredentials: true})
            const {job_id, status} = response.data
            setJobId(job_id)
            setJobStatus(status)

            pollJobStatus(job_id)
        } catch (e) {
            setLoading(false)
            setError(e.response?.data?.detail || `Failed to generate story: ${e.message}`)
        }
    }

    const reset = () => {
        setJobId(null)
        setJobStatus(null)
        setError(null)
        setTheme("")
        setLoading(false)
    }

    return <div className="story-generator">
        {error && <div className="error-message">
            <p>{error}</p>
            <button onClick={reset}>Try Again</button>
        </div>}

        {!jobId && !error && !loading && <ThemeInput onSubmit={generateStory} user={user}/>}

        {loading && <LoadingStatus theme={theme} />}
    </div>
}

export default StoryGenerator
