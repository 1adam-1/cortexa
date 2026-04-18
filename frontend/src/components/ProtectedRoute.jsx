import { Navigate } from "react-router-dom";

export function ProtectedRoute({ children }) {
    // Check for either 'access_token' or 'token' depending on how you stored it in login
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");
    
    if (!token) {
        // Redirect to the login page and replace the URL in history
        return <Navigate to="/auth" replace />;
    }

    return children;
}
