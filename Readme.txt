# ResumeEnhancer

ResumeEnhancer is a full-stack platform that analyzes resumes against job descriptions to provide a match score and suggest improvements. It helps job seekers tailor their resumes and recruiters screen applications more efficiently.

## Tech Stack

-   **Frontend**: React
-   **Backend**: Python, FastAPI
-   **NLP / AI**: spaCy, Scikit-learn
-   **Database**: (Planned - e.g., PostgreSQL/SQLite)

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You will need the following software installed on your machine:

-   [Python 3.8+](https://www.python.org/downloads/)
-   [Node.js v16+](https://nodejs.org/en/download/) (which includes npm)

### Installation

Follow these steps to set up your development environment.

1.  **Clone the repository**
    ```sh
    git clone <your-repository-url>
    cd ResumeEnhancer
    ```

2.  **Set up the Backend (FastAPI)**
    ```sh
    # Navigate to the backend directory
    cd backend

    # Create and activate a Python virtual environment
    # On macOS/Linux:
    python3 -m venv venv
    source venv/bin/activate

    # On Windows:
    python -m venv venv
    .\venv\Scripts\activate

    # Install the required Python packages
    pip install -r requirements.txt
    ```

3.  **Set up the Frontend (React)**
    ```sh
    # Navigate to the frontend directory from the root
    cd ../frontend

    # Install the required npm packages
    npm install
    ```

## Running the Application

You will need to run the backend and frontend servers in two separate terminals.

### 1. Run the Backend Server

-   Make sure you are in the `/backend` directory and your virtual environment is active.
-   Run the FastAPI development server:
    ```sh
    uvicorn main:app --reload
    ```
-   The backend will be running at `http://127.0.0.1:8000`.
-   You can access the API documentation at `http://127.0.0.1:8000/docs`.

### 2. Run the Frontend Server

-   In a new terminal, navigate to the `/frontend` directory.
-   Run the React development server:
    ```sh
    npm start
    ```
-   The frontend will open and run at `http://localhost:3000`.

## Project Structure

    .
    ├── backend
    │   ├── venv/
    │   ├── main.py
    │   └── requirements.txt
    ├── frontend
    │   ├── node_modules/
    │   ├── public/
    │   ├── src/
    │   └── package.json
    ├── .gitignore
    └── README.md