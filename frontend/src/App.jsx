import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Landing from "./Landing";
import AgentApp from "./AgentApp";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AgentApp />} />
      </Routes>
    </Router>
  );
}

export default App;
