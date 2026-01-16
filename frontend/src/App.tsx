import { Routes, Route, BrowserRouter as Router } from "react-router-dom";
import HomePage from "./pages/HomePage";
import EpisodePage from "./pages/EpisodePage";
import AnnotationPage from "./pages/AnnotationPage";
import HarmonizePage from './pages/HarmonizePage';

function App() {
  return (
    <div className="container">
      <header className="mb-24">
        <h1 className="text-primary">ClusterMark</h1>
      </header>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/episodes/:episodeId" element={<EpisodePage />} />
        <Route path="/episodes/:episodeId/harmonize" element={<HarmonizePage />} />
        <Route path="/annotate/:clusterId" element={<AnnotationPage />} />
      </Routes>
    </div>
  );
}

export default App;
