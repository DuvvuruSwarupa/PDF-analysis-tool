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
            return response.json();
        })
        .then(data => {
            const outputBox = document.querySelector('#outputBox');
            if (data.message) {
                if (data.questions) {
                    outputBox.innerHTML = renderQuestions(data.questions);
                } else {
                    outputBox.textContent = data.message;
                }
            }
        })
        .catch(error => {
            const outputBox = document.querySelector('#outputBox');
            outputBox.textContent = 'Error: ' + error;
            alert('Error: ' + error);
            console.error('Error:', error);
        });
    });
});

function renderQuestions(questions) {
    let html = '<h2>Generated Questions</h2>';

    for (const [category, qs] of Object.entries(questions)) {
        html += `<h3>${capitalize(category.replace('_', ' '))} Questions</h3><ul>`;
        qs.forEach(q => {
            html += '<li>';
            if (category === 'multiple_choice') {
                html += `<strong>Question:</strong> ${q.question}<br>`;
                q.options.forEach(option => {
                    html += `<strong>Option:</strong> ${option}<br>`;
                });
                html += `<strong>Answer:</strong> ${q.answer}`;
            } else {
                html += `<strong>Question:</strong> ${q.question}<br><strong>Answer:</strong> ${q.answer}`;
            }
            html += '</li>';
        });
        html += '</ul>';
    }

    return html;
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
