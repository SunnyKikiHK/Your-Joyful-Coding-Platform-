import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

export default function Navbar() {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const navigate = useNavigate();
    
    const avatarUrl = `${api.defaults.baseURL}/static/avatars/default.png`;

    const handleLogout = () => {
        //remove the jwt token from local storage
        localStorage.removeItem('token');
        //redirect the user back to the login page
        navigate('/login');
    };

    return (
        <nav className="navbar">
            <div className="nav-left">
                <Link to="/problems" className="nav-link">Problems</Link>
                <Link to="/discussions" className="nav-link">Discussions</Link>
                <Link to="/insights" className="nav-link">Insights</Link>
            </div>
            
            <div className="nav-right">
                <div className="profile-container">
                    <img 
                        src={avatarUrl} 
                        alt="User Profile" 
                        className="profile-pic"
                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    />
                    
                    {/* pfp drop down menu */}
                    {isDropdownOpen && (
                        <div className="dropdown-menu">
                            <Link 
                                to="/profiles" 
                                className="dropdown-item"
                                onClick={() => setIsDropdownOpen(false)}
                            >
                                Profiles
                            </Link>
                            <button 
                                onClick={handleLogout} 
                                className="dropdown-item logout-dropdown-btn"
                            >
                                Log out
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}