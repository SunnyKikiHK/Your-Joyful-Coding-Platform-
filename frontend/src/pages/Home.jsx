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
            const decoded = jwtDecode(token);
            setUsername(decoded.sub);
        } catch (error) {
            localStorage.removeItem('token');
            navigate('/login');
        }
    }, [navigate]);

    return (
        <div className="container">
            <div className="card">
                <h1>Dashboard</h1>
                <p>Welcome back, <strong>{username}</strong>!</p>
                {/* Redundant Log Out button removed! */}
            </div>
        </div>
    );
}