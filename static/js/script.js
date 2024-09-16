function showFileName() {
  const fileInput = document.getElementById("pdf_file");
  const fileName = fileInput.files[0] ? fileInput.files[0].name : "";
  document.getElementById("fileName").innerText = fileName
    ? `Selected File: ${fileName}`
    : "";
}

function toggleLoading(show) {
  document.getElementById("spinnerContainer").style.display = show
    ? "flex"
    : "none";
  document.body.classList.toggle("blur", show); // Add or remove blur effect
}

function submitPdf() {
  const fileInput = document.getElementById("pdf_file");

  // Validate if a file is selected
  if (!fileInput.files.length) {
    alert("Please select a PDF file to upload.");
    return;
  }

  toggleLoading(true); // Show spinner and apply blur

  const formData = new FormData();
  formData.append("pdf_file", fileInput.files[0]);

  fetch("/process_pdf", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      showAlert("PDF Processed successfully");
    })
    .catch((error) => {
      document.getElementById("summary").innerText = "Error: " + error;
    })
    .finally(() => {
      toggleLoading(false); // Hide spinner and remove blur
    });
}

function summarizePdf(type) {
  const fileInput = document.getElementById("pdf_file");

  if (!fileInput.files.length) {
    alert("Please select a PDF file to summarize.");
    return;
  }

  toggleLoading(true); // Show spinner and apply blur

  const formData = new FormData();
  formData.append("pdf_file", fileInput.files[0]);
  formData.append("summary_type", type);

  fetch("/summarize_pdf", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("summary").innerText =
        data.summary || data.error;
    })
    .catch((error) => {
      document.getElementById("summary").innerText = "Error: " + error;
    })
    .finally(() => {
      toggleLoading(false); // Hide spinner and remove blur
    });
}

function askQuestion() {
  const question = document.getElementById("question").value;

  if (!question) {
    alert("Please enter a question.");
    return;
  }

  toggleLoading(true); // Show spinner and apply blur

  fetch("/ask_question", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  })
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("response").innerText =
        data.response || data.error;
    })
    .catch((error) => {
      document.getElementById("response").innerText = "Error: " + error;
    })
    .finally(() => {
      toggleLoading(false); // Hide spinner and remove blur
    });
}

function fetchOrgInfo() {
  const fileInput = document.getElementById('pdf_file');
  
  if (fileInput.files.length === 0) {
    alert("Please upload a PDF file first.");
    return;
  }

  const formData = new FormData();
  formData.append('pdf_file', fileInput.files[0]);

  toggleLoading(true); // Show spinner and apply blur

  fetch('/fetch_org_info', {
    method: 'POST',
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
      } else {
        document.getElementById('orgInfo').innerText = data.orgInfo;
      }
    })
    .catch(error => {
      console.error('Error:', error);
      document.getElementById('orgInfo').innerText = "Error: " + error;
    })
    .finally(() => {
      toggleLoading(false); // Hide spinner and remove blur
    });
}

function showAlert(message) {
  const alertElement = document.getElementById("alertMessage");
  alertElement.innerText = message;
  alertElement.classList.remove("hide");
  alertElement.classList.add("show");

  setTimeout(() => {
    alertElement.classList.remove("show");
    alertElement.classList.add("hide");
  }, 3000);
}

function startVoiceInput() {
  if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      document.getElementById('audioInputBtn').innerText = 'Listening...';
    };

    recognition.onresult = function (event) {
      const voiceInput = event.results[0][0].transcript;
      document.getElementById('question').value = voiceInput;
      document.getElementById('audioInputBtn').innerText = '🎤 Voice Input';
    };

    recognition.onerror = function () {
      document.getElementById('audioInputBtn').innerText = '🎤 Voice Input';
      alert('Voice recognition failed. Please try again.');
    };

    recognition.start();
  } else {
    alert('Voice recognition not supported in this browser.');
  }
}
