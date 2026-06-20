import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import api from '../api/axiosConfig';

export default function ProblemWorkspace() {
    const { id } = useParams();
    const navigate = useNavigate();
    
    const [question, setQuestion] = useState(null);
    const [code, setCode] = useState('# Write your Python solution here\n\n');
    const [output, setOutput] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const fetchQuestion = async () => {
            try {
                const response = await api.get(`/questions/${id}`);
                setQuestion(response.data);
                // Pre-fill the editor with a function stub based on the title
                const functionName = response.data.title.replace(/\s+/g, '').toLowerCase();
                setCode(`def ${functionName}(...):\n    # TODO: Implement solution\n    pass\n`);
            } catch (error) {
                console.error("Failed to fetch question", error);
                navigate('/');
            }
        };

        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
        } else {
            fetchQuestion();
        }
    }, [id, navigate]);

    const handleRunCode = async () => {
        setIsSubmitting(true);
        setOutput(null);
        try {
            const response = await api.post('/submissions/run', {
                question_id: parseInt(id),
                code: code
            });
            setOutput(response.data);
        } catch (error) {
            setOutput({ status: "System Error", error_message: "Failed to connect to execution engine." });
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!question) return <div className="loading-state">Loading workspace...</div>;

    return (
        <div className="workspace-container">
            {/* LEFT PANEL: Problem Description */}
            <div className="workspace-panel description-panel">
                
                {/* NEW: Back Button */}
                <button className="workspace-back-btn" onClick={() => navigate('/')}>
                    &larr; Back to Problems
                </button>

                <div className="panel-header">
                    <h1 className="workspace-title">{question.title}</h1>
                    <span className={`difficulty-badge ${question.difficulty.toLowerCase()}`}>
                        {question.difficulty}
                    </span>
                </div>
                
                <div className="workspace-topics">
                    {question.topics && question.topics.map(topic => (
                        <span key={topic} className="topic-pill">{topic}</span>
                    ))}
                </div>

                <div className="workspace-description">
                    <p>{question.description}</p>
                </div>

                <div className="workspace-testcases">
                    <h3>Example Test Cases</h3>
                    {question.test_cases && question.test_cases.map((tc, idx) => (
                        <div key={idx} className="testcase-card">
                            <p><strong>Input:</strong> {tc.input}</p>
                            <p><strong>Expected:</strong> {tc.expected_output}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* RIGHT PANEL: Code Editor & Console */}
            <div className="workspace-panel editor-panel">
                <div className="editor-header">
                    <select className="difficulty-select language-select" disabled>
                        <option value="python">Python 3</option>
                    </select>
                    <button 
                        className="run-btn" 
                        onClick={handleRunCode}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Running...' : 'Run Code'}
                    </button>
                </div>

                <div className="monaco-wrapper">
                    <Editor
                        height="100%"
                        defaultLanguage="python"
                        theme="vs-dark"
                        value={code}
                        onChange={(value) => setCode(value)}
                        options={{
                            minimap: { enabled: false },
                            fontSize: 14,
                            padding: { top: 16 }
                        }}
                    />
                </div>

                {/* OUTPUT CONSOLE */}
                <div className="console-panel">
                    <div className="console-header">Output Console</div>
                    <div className="console-body">
                        {!output ? (
                            <span className="console-placeholder">Run your code to see results here.</span>
                        ) : (
                            <div className={`console-result ${output.status === 'Accepted' ? 'success' : 'error'}`}>
                                <h3 className="result-status">{output.status}</h3>
                                {output.message && <p>{output.message}</p>}
                                
                                {output.status === "Wrong Answer" && (
                                    <div className="error-details">
                                        <p><strong>Failed at Test Case {output.failed_case_index + 1}</strong></p>
                                        <p>Expected: <code>{output.expected}</code></p>
                                        <p>Actual: <code>{output.actual}</code></p>
                                    </div>
                                )}

                                {output.status === "Runtime Error" && (
                                    <div className="error-details">
                                        <pre>{output.error_message}</pre>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}