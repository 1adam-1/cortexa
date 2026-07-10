import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import './App.css';
import { Navbar } from "./components/navbar/Navbar.jsx";
import Notebooks from "./components/notebooks/Notebooks.jsx";
import Notebook from "./components/Notebook/Notebook.jsx";
import Auth from "./components/auth/Auth.jsx";
import EvaluationPage from "./components/evaluation/EvaluationPage.jsx";
import Profile from "./components/profile/Profile.jsx";
import Settings from "./components/settings/Settings.jsx";

import { ProtectedRoute } from "./components/ProtectedRoute.jsx";

function App() {
  const location = useLocation();
  const showNavbar = location.pathname !== '/auth';

  return (
    <>
      {showNavbar && <Navbar />}
      <Routes>
        <Route 
          path="/Notebooks" 
          element={
            <ProtectedRoute>
              <Notebooks />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/Notebook/:sessionId" 
          element={
            <ProtectedRoute>
              <Notebook />
            </ProtectedRoute>
          } 
        />
        <Route
          path="/evaluation"
          element={
            <ProtectedRoute>
              <EvaluationPage />
            </ProtectedRoute>
          }
        />
        <Route path="/auth" element={<Auth />} />
        {/* Redirect root to auth by default */}
        <Route path="/" element={<Navigate to="/auth" replace />} />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  )
}

export default App;
