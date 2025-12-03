import './App.css'
import {BrowserRouter as Router, Routes, Route} from "react-router-dom"
import StoryLoader from "./components/StoryLoader"
import StoryGenerator from "./components/StoryGenerator.jsx";
import StorySidebar from "./components/StorySidebar.jsx";

function App() {
  return (
    <Router>
      <div className="app-container">
        <StorySidebar />
        <div className="main-content">
          <header>
            <h1>Interactive Story Generator</h1>
          </header>
          <main>
            <Routes>
              <Route path={"/story/:id"} element={<StoryLoader />} />
              <Route path={"/"} element={<StoryGenerator />}/>
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App
