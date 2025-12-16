const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const uploadForm = document.getElementById('uploadForm');
const selectedFileContainer = document.getElementById('selectedFileContainer');
const progressContainer = document.getElementById('progressContainer');

// Prevent default drag behavior
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
    dropZone.addEventListener(event, e => {
        e.preventDefault();
        e.stopPropagation();
    });
});

['dragenter', 'dragover'].forEach(event => {
    dropZone.addEventListener(event, () => dropZone.classList.add('dragging'));
});

['dragleave', 'drop'].forEach(event => {
    dropZone.addEventListener(event, () => dropZone.classList.remove('dragging'));
});

dropZone.addEventListener('drop', e => {
    fileInput.files = e.dataTransfer.files;
    showFile(fileInput.files[0]);
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        showFile(fileInput.files[0]);
    }
});

function showFile(file) {
    const size = (file.size / 1024).toFixed(2);
    selectedFileContainer.innerHTML =
        `<strong>${file.name}</strong> (${size} KB)`;
}

uploadForm.addEventListener('submit', () => {
    progressContainer.style.display = 'flex';
});
