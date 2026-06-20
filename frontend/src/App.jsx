import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import ProblemWorkspace from './pages/ProblemWorkspace'; // 1. IMPORT HERE
import Layout from './components/Layout';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                
                <Route element={<Layout />}>
                    <Route path="/" element={<Home />} />
                    {/* 2. ADD ROUTE HERE */}
                    <Route path="/problems/:id" element={<ProblemWorkspace />} /> 
                </Route>

                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </Router>
    );
}

export default App;