# Knowledge Base Analysis App

This is a Flask-based web application that allows users to configure connectors for various applications (Freshservice, ServiceNow, SharePoint) and analyze knowledge base articles for compatibility.<br>
**Note**- Add .env file before running the app.

---

## Features

- **Configure connectors** for supported applications.
- **Run analysis** to evaluate knowledge base articles for compatibility.
- **View analysis results** in a user-friendly HTML table format.

---

## Prerequisites

- **Python**: Version 3.8 or above
- **pip**: Python package manager
- **Virtual Environment** (optional but recommended)

---

## Installation and Setup

### Step 1: Download the Application

- Download the ZIP file containing the project source code from the GitHub repository.
- Extract the contents of the ZIP file to a folder on your local machine.
- Open your terminal or command prompt in the folder where you extracted the ZIP file.

### Step 2: Set up a Virtual Environment (Recommended)

**On macOS/Linux**:

```
python3 -m venv venv
source venv/bin/activate
```

**On Windows (Command Prompt)**:

```
python -m venv venv
venv\Scripts\activate
```

**On Windows (PowerShell)**:

```
python -m venv venv
.\venv\Scripts\Activate
```

### Step 3: Install Dependencies

```
pip install -r requirements.txt
```

---

## Running the Application

Run the following command in the terminal/command prompt
```
flask run --debug --host=localhost --port=8000
```
Once the application is running, open your browser and navigate to:

`http://localhost:8000`

---

## Using the Application

1. Navigate to the Admin Page:

- Open your browser and go to `http://localhost:8000`.
- Select an application from the dropdown menu.
- Fill in the necessary connection details (e.g., API Key, Instance, etc.).
- Click Run Analysis to trigger the analysis process.

2. View Analysis Results:

- After running the analysis, the app redirects you to the Analysis Page.
- The analysis results display compatibility details for the knowledge base articles.

---

## Stopping the Application

To stop the Flask server, press `CTRL+C` in the terminal where the app is running.
