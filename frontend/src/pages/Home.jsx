import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

export default function Home() {
    const [questions, setQuestions] = useState([]);
    
    // Filter States
    const [searchQuery, setSearchQuery] = useState('');
    const [difficultyFilter, setDifficultyFilter] = useState('All');
    const [selectedTopics, setSelectedTopics] = useState([]);
    
    // Pagination States
    const [currentPage, setCurrentPage] = useState(1);
    const [pageInput, setPageInput] = useState(1);
    const questionsPerPage = 50;

    const navigate = useNavigate();

    // Fetch questions on mount
    useEffect(() => {
        const fetchQuestions = async () => {
            try {
                // We request a large limit so we can filter and paginate smoothly on the client side
                const response = await api.get('/questions/?skip=0&limit=1000');
                setQuestions(response.data);
            } catch (error) {
                console.error("Failed to fetch questions", error);
            }
        };
        
        // Ensure user is authenticated
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
        } else {
            fetchQuestions();
        }
    }, [navigate]);

    // Dynamically extract all unique topics from the available questions
    const allTopics = [...new Set(questions.flatMap(q => q.topics || []))].sort();

    // Toggle multi-select topics
    const toggleTopic = (topic) => {
        setSelectedTopics(prev => 
            prev.includes(topic) 
                ? prev.filter(t => t !== topic) 
                : [...prev, topic]
        );
    };

    // Advanced Client-Side Filtering Logic
    const filteredQuestions = questions.filter(q => {
        const matchesSearch = 
            q.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
            (q.topics && q.topics.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())));
        
        const matchesDifficulty = difficultyFilter === 'All' || q.difficulty === difficultyFilter;
        
        // If topics are selected, the question MUST contain ALL selected topics
        const matchesTopics = selectedTopics.length === 0 || 
            selectedTopics.every(t => q.topics && q.topics.includes(t));

        return matchesSearch && matchesDifficulty && matchesTopics;
    });

    // Reset to page 1 whenever filters change
    useEffect(() => {
        setCurrentPage(1);
        setPageInput(1);
    }, [searchQuery, difficultyFilter, selectedTopics]);

    // Pagination Logic
    const totalPages = Math.ceil(filteredQuestions.length / questionsPerPage) || 1;
    const paginatedQuestions = filteredQuestions.slice(
        (currentPage - 1) * questionsPerPage, 
        currentPage * questionsPerPage
    );

    const handlePageSubmit = (e) => {
        e.preventDefault();
        const newPage = parseInt(pageInput, 10);
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
        } else {
            setPageInput(currentPage); // Revert if invalid
        }
    };

    return (
        <div className="dashboard-container">
            <h1 className="dashboard-title">Problem Set</h1>

            {/* CONTROL PANEL: Search & Filters */}
            <div className="control-panel">
                <div className="search-row">
                    <input 
                        type="text" 
                        placeholder="Search questions or topics..." 
                        className="search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <select 
                        className="difficulty-select"
                        value={difficultyFilter}
                        onChange={(e) => setDifficultyFilter(e.target.value)}
                    >
                        <option value="All">All Difficulties</option>
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                    </select>
                </div>

                <div className="topics-row">
                    <span className="topics-label">Filter by Topic:</span>
                    <div className="topics-container">
                        {allTopics.map(topic => (
                            <button 
                                key={topic} 
                                className={`topic-pill ${selectedTopics.includes(topic) ? 'active' : ''}`}
                                onClick={() => toggleTopic(topic)}
                            >
                                {topic}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* QUESTIONS TABLE */}
            <div className="table-container">
                <table className="questions-table">
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Title</th>
                            <th>Difficulty</th>
                            <th>Topics</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedQuestions.length > 0 ? (
                            paginatedQuestions.map((q) => (
                                <tr key={q.id} className="question-row" onClick={() => navigate(`/problems/${q.id}`)}>
                                    <td><div className="status-circle unsolved"></div></td>
                                    <td className="question-title">{q.title}</td>
                                    <td>
                                        <span className={`difficulty-badge ${q.difficulty.toLowerCase()}`}>
                                            {q.difficulty}
                                        </span>
                                    </td>
                                    <td className="question-topics">
                                        {q.topics && q.topics.join(', ')}
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan="4" className="no-results">No questions found matching your criteria.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* PAGINATION CONTROLS */}
            <div className="pagination-container">
                <button 
                    className="page-btn" 
                    disabled={currentPage === 1}
                    onClick={() => { setCurrentPage(p => p - 1); setPageInput(currentPage - 1); }}
                >
                    Previous
                </button>
                
                <form onSubmit={handlePageSubmit} className="page-form">
                    <span>Page</span>
                    <input 
                        type="number" 
                        min="1" 
                        max={totalPages} 
                        value={pageInput}
                        onChange={(e) => setPageInput(e.target.value)}
                        className="page-input"
                    />
                    <span>of {totalPages}</span>
                    <button type="submit" className="go-btn" style={{display: 'none'}}>Go</button>
                </form>

                <button 
                    className="page-btn" 
                    disabled={currentPage === totalPages}
                    onClick={() => { setCurrentPage(p => p + 1); setPageInput(currentPage + 1); }}
                >
                    Next
                </button>
            </div>
        </div>
    );
}