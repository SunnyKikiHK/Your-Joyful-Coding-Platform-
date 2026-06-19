import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import Layout from './components/Layout';

function App() {
    return (
        <Router>
            <Routes>
                {/* Public Routes (No Navbar) */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                
                {/* Protected Routes (Wrapped in Layout with Navbar) */}
                <Route element={<Layout />}>
                    <Route path="/" element={<Home />} />
                    {/* Future routes like /problems will go here */}
                </Route>

                {/* Catch any unknown routes and send them home */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Router>
    );
}

export default App;