// Configure Monaco loader
require.config({ 
    paths: { 
        'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.43.0/min/vs'
    }
});

// Configure worker
window.MonacoEnvironment = {
    getWorkerUrl: function(workerId, label) {
        return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
            self.MonacoEnvironment = {
                baseUrl: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.43.0/min/'
            };
            importScripts('https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.43.0/min/vs/base/worker/workerMain.js');`
        )}`;
    }
};

let editor;
let currentLanguage = 'python';
let activeFile = null;

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load Monaco and initialize the repository view
    require(['vs/editor/editor.main'], function() {
        initializeEditor();
        loadSkeletonRepository();
    });
});

function initializeEditor() {
    // Make sure container exists
    const container = document.getElementById('monacoEditor');
    if (!container) {
        console.error('Editor container not found');
        return;
    }

    // Set initial container size
    container.style.height = '100%';
    container.style.width = '100%';
    container.style.float = '';

    // Create editor with updated options
    editor = monaco.editor.create(container, {
        value: '# Select a skeleton file from the repository to begin\n',
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true, // Let Monaco handle layout
        minimap: {
            enabled: true
        },
        fontSize: 14,
        lineNumbers: 'on',
        roundedSelection: false,
        scrollBeyondLastLine: false,
        readOnly: false,
        cursorStyle: 'line',
        scrollbar: {
            vertical: 'visible',
            horizontal: 'visible',
            horizontalScrollbarSize: 12,
            verticalScrollbarSize: 12
        },
        fixedOverflowWidgets: true,
        wordWrap: 'on',
        wrappingIndent: 'indent'
    });

    // Initial layout update
    editor.layout();

    // Handle window resize
    window.addEventListener('resize', function() {
        if (editor) {
            editor.layout();
        }
    });

    // Setup event listeners
    setupEventListeners();
}

function loadSkeletonRepository() {
    // Get or create loading container
    let loadingContainer = document.querySelector('.loading-container');
    if (!loadingContainer) {
        loadingContainer = document.createElement('div');
        loadingContainer.className = 'loading-container';
        const repoList = document.getElementById('repoList');
        repoList.parentNode.insertBefore(loadingContainer, repoList);
    }
    
    loadingContainer.textContent = 'Loading skeleton repository...';
    
    fetch('/dev/skeletons/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const repoList = document.getElementById('repoList');
                if (!repoList) {
                    console.error('repoList element not found');
                    loadingContainer.textContent = 'Error: Repository list container not found';
                    return;
                }
                
                repoList.innerHTML = ''; // Clear existing content
                
                if (!data.data || data.data.length === 0) {
                    loadingContainer.textContent = 'No skeleton files found in repository';
                    return;
                }
                
                loadingContainer.textContent = 'Repository loaded successfully';
                
                data.data.forEach(folder => {
                    const folderElement = createFolderElement(folder);
                    repoList.appendChild(folderElement);
                });
            } else {
                loadingContainer.textContent = 'Error loading repository: ' + data.error;
            }
        })
        .catch(error => {
            loadingContainer.textContent = 'Error loading repository: ' + error;
        });
}

function createFolderElement(folder) {
    console.log('Creating folder element:', folder);
    
    const folderDiv = document.createElement('div');
    folderDiv.className = 'skeleton-folder';
    
    // Create folder header
    const folderHeader = document.createElement('div');
    folderHeader.className = 'skeleton-item';
    
    // Use a more modern folder icon and ensure the name is displayed
    folderHeader.innerHTML = `
        <span class="skeleton-icon">🗂️</span>
        <span>${folder.name || 'Unnamed Folder'}</span>
    `;
    folderDiv.appendChild(folderHeader);

    // Create container for children
    const childrenContainer = document.createElement('div');
    childrenContainer.style.marginLeft = '20px';
    childrenContainer.style.display = 'none'; // Hidden by default

    // Add files
    folder.children.forEach(file => {
        const fileElement = createFileElement(file);
        childrenContainer.appendChild(fileElement);
    });

    folderDiv.appendChild(childrenContainer);

    // Toggle folder on click
    folderHeader.addEventListener('click', () => {
        childrenContainer.style.display = 
            childrenContainer.style.display === 'none' ? 'block' : 'none';
    });

    return folderDiv;
}

function createFileElement(file) {
    console.log('Creating file element:', file);
    
    const fileDiv = document.createElement('div');
    fileDiv.className = 'skeleton-item skeleton-file';
    
    // Get file extension to show appropriate icon
    const extension = file.name.split('.').pop().toLowerCase();
    let icon = '📄';
    if (extension === 'py') icon = '🐍';
    else if (extension === 'cpp' || extension === 'h') icon = '⚡';
    
    fileDiv.innerHTML = `
        <span class="skeleton-icon">${icon}</span>
        <span>${file.name || 'Unnamed File'}</span>
    `;

    fileDiv.addEventListener('click', () => {
        console.log('File clicked:', file.path);
        // Add active class to clicked file and remove from others
        document.querySelectorAll('.skeleton-file').forEach(el => el.classList.remove('active'));
        fileDiv.classList.add('active');
        loadFile(file.path);
    });
    return fileDiv;
}

function loadFile(path) {
    fetch(`/dev/skeletons/${path}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                activeFile = path;
                editor.setValue(data.content);
                monaco.editor.setModelLanguage(editor.getModel(), data.language);
                currentLanguage = data.language;
                
                // Update language selector if it exists
                const languageSelect = document.getElementById('languageSelect');
                if (languageSelect) {
                    languageSelect.value = data.language;
                }
                
                showOutput(`Loaded: ${path}`, 'success');
            } else {
                showOutput('Error loading file: ' + data.error, 'error');
            }
        })
        .catch(error => {
            showOutput('Error loading file: ' + error, 'error');
        });
}

function setupEventListeners() {
    // Setup resize functionality
    const resizeHandle = document.getElementById('resize-handle');
    const sidebar = document.getElementById('sidebar');
    let isResizing = false;
    let startX;
    let startWidth;

    if (resizeHandle && sidebar) {
        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.pageX;
            startWidth = sidebar.offsetWidth;
            resizeHandle.classList.add('active');
            
            // Add temporary event listeners
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', () => {
                isResizing = false;
                resizeHandle.classList.remove('active');
                document.removeEventListener('mousemove', handleMouseMove);
            }, { once: true });
        });

        function handleMouseMove(e) {
            if (!isResizing) return;
            
            const width = startWidth + (e.pageX - startX);
            const containerWidth = sidebar.parentElement.offsetWidth;
            const minWidth = 150; // Minimum sidebar width
            const maxWidth = containerWidth * 0.8; // Maximum 80% of container
            
            // Constrain width between min and max
            const newWidth = Math.min(Math.max(width, minWidth), maxWidth);
            sidebar.style.width = `${newWidth}px`;
            
            // Ensure editor layout updates
            if (editor) {
                editor.layout();
            }
        }
    }

    // Language change handler
    const languageSelect = document.getElementById('languageSelect');
    languageSelect.style.marginTop = '75px';
    if (languageSelect) {
        languageSelect.addEventListener('change', function(e) {
            currentLanguage = e.target.value;
            if (editor) {
                monaco.editor.setModelLanguage(editor.getModel(), currentLanguage);
            }
        });
    }

    // Save button handler
    const saveButton = document.getElementById('saveButton');
    if (saveButton) {
        saveButton.addEventListener('click', saveCode);
    }

    // Run button handler
    const runButton = document.getElementById('runButton');
    if (runButton) {
        runButton.addEventListener('click', runCode);
    }
}


function saveCode() {
    if (!editor) {
        console.error('Editor not initialized');
        return;
    }

    const code = editor.getValue();
    const language = currentLanguage;

    fetch('/dev/save-code/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            code: code,
            language: language,
            file_path: activeFile
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showOutput('Code saved successfully!', 'success');
        } else {
            showOutput('Error saving code: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showOutput('Error saving code: ' + error, 'error');
    });
}

function runCode() {
    if (!editor) {
        console.error('Editor not initialized');
        return;
    }

    const code = editor.getValue();
    const language = currentLanguage;

    showOutput('Running code...\n', 'normal');

    fetch('/dev/run-code/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            code: code,
            language: language
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showOutput(data.output, 'success');
        } else {
            showOutput('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showOutput('Error running code: ' + error, 'error');
    });
}

function showOutput(message, type) {
    // Update repository status if it's a repository message
    if (message.includes('Repository') || message.includes('skeleton repository')) {
        const repoStatus = document.getElementById('repoStatus');
        if (repoStatus) {
            repoStatus.textContent = message;
            repoStatus.className = 'repo-status ' + type;
        }
    }
    
    // Show in console
    const console = document.getElementById('outputConsole');
    if (console) {
        const output = document.createElement('div');
        output.classList.add(type);
        output.textContent = message;
        console.appendChild(output);
        console.scrollTop = console.scrollHeight;
    }
}

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