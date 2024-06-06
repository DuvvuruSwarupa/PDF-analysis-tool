document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#uploadForm').addEventListener('submit', function(event) {
        event.preventDefault();

        const fileInput = document.querySelector('#pdfFile');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('No file chosen. Please select a PDF file to upload.');
            return;
        }

        if (!file.name.endsWith('.pdf')) {
            alert('Invalid file format. Please upload a PDF file.');
            return;
        }

        const formData = new FormData();
        formData.append('pdfFile', file);

        fetch('http://127.0.0.1:5001/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const downloadLink = document.querySelector('#downloadLink');
            downloadLink.href = url;
            downloadLink.download = 'generated_questions.pdf';
            downloadLink.style.display = 'block';
            downloadLink.textContent = 'Download Generated PDF';
        })
        .catch(error => {
            const outputBox = document.querySelector('#outputBox');
            outputBox.textContent = 'Error: ' + error;
            alert('Error: ' + error);
            console.error('Error:', error);
        });
    });
});
