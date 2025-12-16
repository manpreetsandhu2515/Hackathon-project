// Drag and drop file upload
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    dropArea.style.borderColor = '#2563eb';
    dropArea.style.backgroundColor = '#f8fafc';
}

function unhighlight() {
    dropArea.style.borderColor = '#e2e8f0';
    dropArea.style.backgroundColor = '';
}

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        updateFileInfo(file);
        fileInput.files = files; // Update the actual file input
    }
}

// Handle file input change
fileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
        updateFileInfo(this.files[0]);
    }
});

function updateFileInfo(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'flex';
    dropArea.querySelector('.upload-prompt').style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Remove file
removeFileBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    fileInput.value = '';
    fileInfo.style.display = 'none';
    dropArea.querySelector('.upload-prompt').style.display = 'block';
});

// Form submission with loading animation
const uploadForm = document.getElementById('upload-form');
const processingOverlay = document.getElementById('processing-overlay');
const submitBtn = document.getElementById('submit-btn');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const processingText = document.getElementById('processing-text');

if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
        // Show processing overlay
        processingOverlay.style.display = 'flex';
        submitBtn.disabled = true;
        
        // Simulate progress (in real app, this would come from server events)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            
            progressBar.style.width = progress + '%';
            progressText.textContent = Math.round(progress) + '% Complete';
            
            // Update processing text
            if (progress < 30) {
                processingText.textContent = 'Validating file format...';
            } else if (progress < 60) {
                processingText.textContent = 'Initializing AI agent...';
            } else {
                processingText.textContent = 'Cleaning and enriching data...';
            }
        }, 500);
        
        // Store interval ID for cleanup
        uploadForm.dataset.progressInterval = progressInterval;
    });
}

// Load sample data
function loadSample() {
    // Create sample CSV content
    const sampleCSV = `name,address,phone,specialty,license,city
Dr. Amit Sharma,Near City Mall,987654,heart doctor,,Delhi
Dr. Priya Patel,14th Cross MG Road,8765432109,dermatologist,KA/12345/2020,Bangalore
Dr. Rajesh Kumar,City Hospital Andheri,7654321098,orthopedic surgeon,MH/67890/2019,Mumbai
Dr. Anjali Mehta,Green Park South Delhi,6543210987,pediatrician,DL/54321/2021,Delhi
Dr. Vikram Singh,Sector 17 Chandigarh,5432109876,neurologist,CH/98765/2018,Chandigarh`;

    // Create a file object
    const blob = new Blob([sampleCSV], { type: 'text/csv' });
    const file = new File([blob], 'sample_providers.csv', { type: 'text/csv' });
    
    // Update file input and info
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    
    updateFileInfo(file);
    
    // Check all AI options
    document.querySelectorAll('.ai-options input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    alert('Sample data loaded! Click "Process with AI Agent" to see it in action.');
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[title]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.title;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            
            this.dataset.tooltipId = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.dataset.tooltipId) {
                this.dataset.tooltipId.remove();
                delete this.dataset.tooltipId;
            }
        });
    });
}

// Add tooltip styles
const tooltipStyle = document.createElement('style');
tooltipStyle.textContent = `
    .tooltip {
        position: fixed;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: 4px;
        font-size: 0.875rem;
        z-index: 10000;
        pointer-events: none;
        max-width: 300px;
        word-wrap: break-word;
    }
    
    .tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: rgba(0, 0, 0, 0.8) transparent transparent transparent;
    }
`;
document.head.appendChild(tooltipStyle);

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    
    // Add animation to logo
    const logoIcon = document.querySelector('.logo-icon');
    if (logoIcon) {
        logoIcon.style.animation = 'pulse 2s infinite';
        
        const pulseAnimation = document.createElement('style');
        pulseAnimation.textContent = `
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
        `;
        document.head.appendChild(pulseAnimation);
    }
});