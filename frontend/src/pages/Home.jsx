import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';

export default function Home() {
    const [username, setUsername] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }

        try {
            // Decode the token to extract the 'sub' (subject) which we set as the username in FastAPI
            const decoded = jwtDecode(token);
            setUsername(decoded.sub);
        } catch (error) {
            localStorage.removeItem('token');
            navigate('/login');
        }
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div className="container">
            <div className="card">
                <h1>Dashboard</h1>
                <p>You are logged in as: <strong>{username}</strong></p>
                <button onClick={handleLogout} className="logout-btn">Log Out</button>
            </div>
        </div>
    );
}