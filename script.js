function uploadFile() {
    const fileInput = document.getElementById('pdfFile');
    const outputBox = document.getElementById('outBox');

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('pdfFile', file);

        fetch('http://127.0.0.1:5001/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('File uploaded successfully');
                outputBox.textContent = 'Questions stored to MongoDB successfully';
                outputBox.style.display = 'block';
            } else {
                alert('Error uploading file or processing.');
            }
        })
        .catch(error => {
            alert('Error uploading file or processing.');
            console.error('Error:', error);
        });
    } else {
        alert('Please select a file to upload.');
    }
}
