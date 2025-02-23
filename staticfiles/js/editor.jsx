import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';
import Editor from '@monaco-editor/react';

function App() {
    const [files, setFiles] = useState([]);
    const [activeFile, setActiveFile] = useState(null);
    const [fileContent, setFileContent] = useState('');
    const [language, setLanguage] = useState('python');
    const [output, setOutput] = useState([]);
    const editorRef = useRef(null);

    // Handle editor mounting
    function handleEditorDidMount(editor, monaco) {
        editorRef.current = editor;
    }

    // Load repository data
    useEffect(() => {
        loadSkeletonRepository();
    }, []);

    // Load repository files
    async function loadSkeletonRepository() {
        try {
            const response = await fetch('/dev/skeletons/');
            const data = await response.json();
            
            if (data.success) {
                setFiles(data.data || []);
                addOutput('Repository loaded successfully', 'success');
            } else {
                addOutput('Error loading repository: ' + data.error, 'error');
            }
        } catch (error) {
            addOutput('Error loading repository: ' + error, 'error');
        }
    }

    // Load file content
    async function loadFile(path) {
        try {
            const response = await fetch(`/dev/skeletons/${path}`);
            const data = await response.json();
            
            if (data.success && data.content) {
                setFileContent(data.content);
                setLanguage(data.language || 'python');
                setActiveFile(path);
                addOutput(`Loaded: ${path}`, 'success');
            } else {
                addOutput('Error loading file: Invalid data', 'error');
            }
        } catch (error) {
            addOutput(`Error loading file: ${error}`, 'error');
        }
    }

    // Save file content
    async function saveCode() {
        if (!editorRef.current || !activeFile) return;

        try {
            const response = await fetch('/dev/save-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    code: editorRef.current.getValue(),
                    language: language,
                    file_path: activeFile
                })
            });
            
            const data = await response.json();
            if (data.success) {
                addOutput('Code saved successfully!', 'success');
            } else {
                addOutput('Error saving code: ' + data.error, 'error');
            }
        } catch (error) {
            addOutput('Error saving code: ' + error, 'error');
        }
    }

    // Run code
    async function runCode() {
        if (!editorRef.current) return;

        addOutput('Running code...\n', 'normal');

        try {
            const response = await fetch('/dev/run-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    code: editorRef.current.getValue(),
                    language: language
                })
            });
            
            const data = await response.json();
            if (data.success) {
                addOutput(data.output, 'success');
            } else {
                addOutput('Error: ' + data.error, 'error');
            }
        } catch (error) {
            addOutput('Error running code: ' + error, 'error');
        }
    }

    // Add output message
    function addOutput(message, type) {
        setOutput(prev => [...prev, { message, type }]);
    }

    // Render file tree item
    function renderFileTree(item) {
        if (item.type === 'directory') {
            return (
                <div key={item.path} className="skeleton-folder">
                    <div className="skeleton-item">
                        <span className="skeleton-icon">🗂️</span>
                        <span>{item.name}</span>
                    </div>
                    <div style={{ marginLeft: '20px' }}>
                        {item.children.map(child => renderFileTree(child))}
                    </div>
                </div>
            );
        }

        return (
            <div
                key={item.path}
                className={`skeleton-item skeleton-file ${activeFile === item.path ? 'active' : ''}`}
                onClick={() => loadFile(item.path)}
            >
                <span className="skeleton-icon">
                    {item.name.endsWith('.py') ? '🐍' : 
                     item.name.endsWith('.cpp') || item.name.endsWith('.h') ? '⚡' : '📄'}
                </span>
                <span>{item.name}</span>
            </div>
        );
    }

    return (
        <div className="dev-container">
            <div className="top-controls">
                <select 
                    className="language-select"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                >
                    <option value="python">Python</option>
                    <option value="cpp">C++</option>
                </select>
                <button className="save-btn" onClick={saveCode}>Save</button>
                <button className="run-btn" onClick={runCode}>Run</button>
            </div>
            
            <div className="content-area">
                <div className="left-panel">
                    <div className="repo-header">
                        <div className="repo-status">
                            {files.length ? 'Repository loaded' : 'Loading...'}
                        </div>
                    </div>
                    <div className="repo-list">
                        {files.map(file => renderFileTree(file))}
                    </div>
                </div>
                
                <div id="resize-handle" className="resize-handle"></div>
                
                <div className="editor-container">
                    <Editor
                        height="90%"
                        defaultLanguage="python"
                        language={language}
                        value={fileContent}
                        theme="vs-dark"
                        options={{
                            minimap: { enabled: true },
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                        }}
                        onMount={handleEditorDidMount}
                    />
                    <div className="output-console">
                        {output.map((item, index) => (
                            <div key={index} className={item.type}>
                                {item.message}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Render the app
ReactDOM.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>,
    document.getElementById('root')
);