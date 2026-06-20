import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

const ALL_TOPICS = [
    "Array", "String", "Hash Table", "Dynamic Programming", "Math", 
    "Sorting", "Greedy", "Depth-First Search", "Binary Search", 
    "Tree", "Matrix", "Two Pointers", "Breadth-First Search"
].sort();

export default function Home() {
    const [questions, setQuestions] = useState([]);
    const [totalQuestions, setTotalQuestions] = useState(0); 
    
    // Initialize state from sessionStorage if it exists, otherwise use defaults
    const [searchQuery, setSearchQuery] = useState(sessionStorage.getItem('searchQuery') || '');
    const [difficultyFilter, setDifficultyFilter] = useState(sessionStorage.getItem('difficultyFilter') || 'All');
    const [selectedTopics, setSelectedTopics] = useState(JSON.parse(sessionStorage.getItem('selectedTopics')) || []);
    const [currentPage, setCurrentPage] = useState(parseInt(sessionStorage.getItem('currentPage')) || 1);
    const [pageInput, setPageInput] = useState(parseInt(sessionStorage.getItem('currentPage')) || 1);
    
    const questionsPerPage = 50;
    const navigate = useNavigate();

    // Save states to sessionStorage whenever they change
    useEffect(() => {
        sessionStorage.setItem('searchQuery', searchQuery);
        sessionStorage.setItem('difficultyFilter', difficultyFilter);
        sessionStorage.setItem('selectedTopics', JSON.stringify(selectedTopics));
        sessionStorage.setItem('currentPage', currentPage);
    }, [searchQuery, difficultyFilter, selectedTopics, currentPage]);

    // Server-Side Fetch Logic
    useEffect(() => {
        const fetchQuestions = async () => {
            try {
                const params = new URLSearchParams({
                    skip: (currentPage - 1) * questionsPerPage,
                    limit: questionsPerPage,
                });

                if (searchQuery) params.append('search', searchQuery);
                if (difficultyFilter !== 'All') params.append('difficulty', difficultyFilter);
                selectedTopics.forEach(t => params.append('topics', t));

                const response = await api.get(`/questions/?${params.toString()}`);
                setQuestions(response.data.items);
                setTotalQuestions(response.data.total);
            } catch (error) {
                if (error.response?.status === 401) {
                    localStorage.removeItem('token');
                    navigate('/login');
                }
                console.error("Failed to fetch questions", error);
            }
        };
        
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
        } else {
            fetchQuestions();
        }
    }, [navigate, currentPage, searchQuery, difficultyFilter, selectedTopics]); 

    // Reset to page 1 whenever search, difficulty, or topics change
    useEffect(() => {
        setCurrentPage(1);
        setPageInput(1);
    }, [searchQuery, difficultyFilter, selectedTopics]);

    const toggleTopic = (topic) => {
        setSelectedTopics(prev => 
            prev.includes(topic) 
                ? prev.filter(t => t !== topic) 
                : [...prev, topic]
        );
    };

    const totalPages = Math.ceil(totalQuestions / questionsPerPage) || 1;

    const handlePageSubmit = (e) => {
        e.preventDefault();
        const newPage = parseInt(pageInput, 10);
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
        } else {
            setPageInput(currentPage);
        }
    };

    return (
        <div className="dashboard-container">
            <h1 className="dashboard-title">Problem Set</h1>

            {/* CONTROL PANEL */}
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
                        {ALL_TOPICS.map(topic => (
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
                        {questions.length > 0 ? (
                            questions.map((q) => (
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