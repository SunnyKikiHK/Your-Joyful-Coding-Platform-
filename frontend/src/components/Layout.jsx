import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
    return (
        <div className="app-layout">
            <Navbar />
            {/* The Outlet is where your Home, Problems, etc. will render */}
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}