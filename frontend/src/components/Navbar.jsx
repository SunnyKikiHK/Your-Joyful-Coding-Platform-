import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axiosConfig';

export default function Navbar() {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    
    //default image URL pointing to your FastAPI static folder
    //fetch the actual user's URL from the backend later
    const avatarUrl = `${api.defaults.baseURL}/static/avatars/default.png`;

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
                    
                    {/* The Empty Dropdown Menu */}
                    {isDropdownOpen && (
                        <div className="dropdown-menu">
                            {/* Dropdown items will go here later */}
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}