import { Routes, Route, useLocation } from 'react-router-dom';
import './App.css';
import { Navbar } from "./components/navbar/Navbar.jsx";
import Notebooks from "./components/notebooks/Notebooks.jsx";
import Notebook from "./components/Notebook/Notebook.jsx";
import Auth from "./components/auth/Auth.jsx";

function App() {
  const location = useLocation();
  const showNavbar = location.pathname !== '/auth';

  return (
    <>
      {showNavbar && <Navbar />}
      <Routes>
        <Route path="/Notebooks/:userId" element={<Notebooks />} />
        <Route path="/Notebook/:sessionId" element={<Notebook />} />
        <Route path="/auth" element={<Auth />} />
      </Routes>
    </>
  )
}

export default App;
