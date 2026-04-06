import { Routes, Route } from 'react-router-dom';
import './App.css';
import { Navbar } from "./components/navbar/Navbar.jsx";
import Notebooks from "./components/notebooks/Notebooks.jsx";
import Notebook from "./components/Notebook/Notebook.jsx";

function App() {

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Notebooks />} />
        <Route path="/Notebook" element={<Notebook />} />
      </Routes>
    </>
  )
}

export default App;
