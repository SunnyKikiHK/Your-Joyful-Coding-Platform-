import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/axiosConfig';

export default function Login() {
    const [formData, setFormData] = useState({ username: '', password: '' });
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // FastAPI's OAuth2PasswordRequestForm requires x-www-form-urlencoded data
        const params = new URLSearchParams();
        params.append('username', formData.username);
        params.append('password', formData.password);

        try {
            const response = await api.post('/auth/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            
            // Save the token to local storage and redirect to home
            localStorage.setItem('token', response.data.access_token);
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed');
        }
    };

    return (
        <div className="container">
            <div className="card">
                <h2>Welcome Back</h2>
                {error && <div className="error">{error}</div>}
                <form onSubmit={handleSubmit}>
                    <input 
                        type="text" 
                        placeholder="Username or Email" 
                        required 
                        value={formData.username}
                        onChange={(e) => setFormData({...formData, username: e.target.value})}
                    />
                    <input 
                        type="password" 
                        placeholder="Password" 
                        required 
                        value={formData.password}
                        onChange={(e) => setFormData({...formData, password: e.target.value})}
                    />
                    <button type="submit">Log In</button>
                </form>
                <p>Need an account? <Link to="/register">Sign up</Link></p>
            </div>
        </div>
    );
}