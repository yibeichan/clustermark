import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import EpisodePage from './pages/EpisodePage'
import AnnotationPage from './pages/AnnotationPage'

function App() {
  return (
    <div className="container">
      <div className="header">
        <h1>ClusterMark</h1>
        <p>Face Cluster Annotation System</p>
      </div>
      
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/episodes/:episodeId" element={<EpisodePage />} />
        <Route path="/episodes/:episodeId/annotate" element={<AnnotationPage />} />
        <Route path="/annotate/:clusterId" element={<AnnotationPage />} />
      </Routes>
    </div>
  )
}

export default App