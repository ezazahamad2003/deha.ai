document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing application...');
    
    // Debug function to log all network requests
    const originalFetch = window.fetch;
    window.fetch = function() {
        console.log('Fetch called with:', arguments);
        return originalFetch.apply(this, arguments)
            .then(response => {
                console.log('Fetch response:', response);
                return response;
            })
            .catch(error => {
                console.error('Fetch error:', error);
                throw error;
            });
    };
    
    const dropZone = document.getElementById('dropZone');
    const pdfUpload = document.getElementById('pdfUpload');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    // Verify elements are found
    console.log('Elements found:', {
        dropZone: !!dropZone,
        pdfUpload: !!pdfUpload,
        chatMessages: !!chatMessages,
        userInput: !!userInput,
        sendBtn: !!sendBtn
    });

    // API endpoints
    const API_BASE_URL = 'http://127.0.0.1:5000';
    console.log('Using API base URL:', API_BASE_URL);

    // Test server connection
    console.log('Testing server connection...');
    fetch(`${API_BASE_URL}/test`)
        .then(response => {
            console.log('Test response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Server test response:', data);
        })
        .catch(error => {
            console.error('Server test error:', error);
            addMessage('AI', 'Error connecting to server. Please try again later.');
        });

    // Handle file upload
    dropZone.addEventListener('click', () => {
        console.log('Drop zone clicked');
        pdfUpload.click();
    });
    
    pdfUpload.addEventListener('change', (e) => {
        console.log('File input changed');
        handleFile(e.target.files[0]);
    });
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    function handleFile(file) {
        if (!file) return;
        
        if (file.type !== 'application/pdf') {
            alert('Please upload a PDF file');
            return;
        }

        const formData = new FormData();
        formData.append('pdf', file);

        // Show loading state
        dropZone.innerHTML = '<div class="upload-icon"><i class="fas fa-spinner fa-spin"></i></div><p>Uploading...</p>';

        console.log('Uploading file:', file.name);
        fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Upload response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Upload response data:', data);
            if (data.success) {
                dropZone.innerHTML = '<div class="upload-icon"><i class="fas fa-check"></i></div><p>PDF uploaded successfully!</p>';
                // Enable chat functionality after successful upload
                userInput.disabled = false;
                sendBtn.disabled = false;
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            dropZone.innerHTML = `
                <div class="upload-icon"><i class="fas fa-cloud-upload-alt"></i></div>
                <p>Click or drag and drop your PDF here</p>
                <input type="file" id="pdfUpload" accept=".pdf" style="display: none;" />
            `;
            alert('Upload failed: ' + error.message);
        });
    }

    // Handle chat functionality
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !userInput.disabled) {
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', () => {
        if (!userInput.disabled) {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage('User', message);
        userInput.value = '';

        // Disable input while waiting for response
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Send message to server
        fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            addMessage('AI', data.response);
        })
        .catch(error => {
            console.error('Chat error:', error);
            addMessage('AI', 'Sorry, I encountered an error. Please try again.');
        })
        .finally(() => {
            // Re-enable input
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        });
    }

    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender.toLowerCase()}-message`;
        
        const contentSpan = document.createElement('span');
        contentSpan.className = 'content';
        contentSpan.textContent = message;
        
        messageDiv.appendChild(contentSpan);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    console.log('Application initialization complete');
}); 