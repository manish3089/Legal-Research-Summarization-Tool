<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Summarization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .container {
            max-width: 400px;
            margin: auto;
            text-align: center;
        }
        input[type="file"] {
            margin: 20px 0;
        }
        button {
            padding: 10px 20px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload PDF for Summarization</h1>
        <input type="file" id="pdfFile" accept="application/pdf">
        <button onclick="uploadPDF()">Upload and Summarize</button>
        <p id="status"></p>
    </div>

    <script>
        function uploadPDF() {
            const fileInput = document.getElementById('pdfFile');
            const status = document.getElementById('status');

            if (!fileInput.files.length) {
                status.textContent = "Please select a PDF file.";
                status.style.color = "red";
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('pdf', file);

            status.textContent = "Uploading...";
            status.style.color = "black";

            // Replace 'your-backend-endpoint' with your actual backend API endpoint
            fetch('your-backend-endpoint', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.summary) {
                    status.textContent = "Summary: " + data.summary;
                    status.style.color = "green";
                } else {
                    status.textContent = "Failed to summarize the PDF.";
                    status.style.color = "red";
                }
            })
            .catch(error => {
                console.error('Error:', error);
                status.textContent = "An error occurred while uploading.";
                status.style.color = "red";
            });
        }
    </script>
</body>
</html>
