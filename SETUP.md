# Quick Setup Guide

## Prerequisites
- Docker and Docker Compose installed
- OpenAI API key from https://platform.openai.com/api-keys

## Step-by-Step Setup

### 1. Create Environment File

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Start with Docker Compose

```bash
docker-compose up --build
```

This will:
- Start PostgreSQL database with sample data
- Start the FastAPI backend on port 8000
- Start the React frontend on port 3000

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Try It Out!

Ask questions like:
- "Show me all users"
- "How many orders were placed?"
- "List users with their order count"
- "What are the top 5 products by sales?"

## Development Mode (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Create .env file with your OpenAI API key
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check database credentials in `.env` file
- Verify port 5432 is not in use

### OpenAI API Errors
- Verify your API key is correct
- Check your OpenAI account has credits
- Ensure the API key has proper permissions

### Frontend Not Connecting to Backend
- Check backend is running on port 8000
- Verify CORS settings in `backend/main.py`
- Check browser console for errors

