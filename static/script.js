document.getElementById('contentForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const contentId = document.getElementById('content_id').value;
    const resultDiv = document.getElementById('result');
    
    fetch('/generate_and_post', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `content_id=${encodeURIComponent(contentId)}`
    })
    .then(response => response.json())
    .then(data => {
        resultDiv.innerHTML = `
            <h2>Results:</h2>
            <p>LinkedIn: ${JSON.stringify(data.linkedin_result)}</p>
            <p>Twitter: ${JSON.stringify(data.twitter_result)}</p>
        `;
    })
    .catch(error => {
        resultDiv.innerHTML = `<p>Error: ${error.message}</p>`;
    });
});