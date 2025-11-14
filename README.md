# Text to SQL Chat Application

A full-stack production-ready application that converts natural language questions into SQL queries using OpenAI GPT-4o-mini. Features a beautiful ChatGPT-like interface built with React and TypeScript.

## Features

- 🤖 **AI-Powered SQL Generation**: Uses OpenAI GPT-4o-mini to convert natural language to SQL
- 💬 **ChatGPT-like Interface**: Beautiful, modern chat UI with smooth animations
- 🔒 **Secure**: Only allows SELECT queries for security
- 📊 **Data Visualization**: View SQL queries and results in an organized table format
- 🐳 **Docker Support**: Fully containerized with Docker Compose
- ⚡ **Fast API**: Built with FastAPI for high performance
- 🎨 **Modern UI**: Responsive design with gradient themes

## Tech Stack

### Backend
- Python 3.11
- FastAPI
- OpenAI API (GPT-4o-mini)
- PostgreSQL
- psycopg2

### Frontend
- React 18
- TypeScript
- Vite
- Axios

### Infrastructure
- Docker & Docker Compose
- PostgreSQL Database

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Quick Start

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Start the application with Docker Compose**

   ```bash
   docker-compose up --build
   ```

4. **Access the application**

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Development Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=postgres
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Database Setup

The application uses PostgreSQL. You can either:

1. **Use Docker Compose** (recommended): The `docker-compose.yml` includes a PostgreSQL service
2. **Use your own PostgreSQL instance**: Update the database configuration in `.env`

### Sample Schema

The application works with any PostgreSQL database. Example schema:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_name VARCHAR(100),
    quantity INTEGER,
    price DECIMAL(10, 2),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

Try asking questions like:

- "Show me all users"
- "How many orders were placed?"
- "List users with their order count"
- "What are the top 5 products by sales?"
- "Show me users who placed orders in the last month"

## API Endpoints

### POST `/api/chat`
Convert natural language to SQL and execute it.

**Request:**
```json
{
  "message": "Show me all users",
  "conversation_history": []
}
```

**Response:**
```json
{
  "message": "I found 10 result(s). Here's the data:",
  "sql_query": "SELECT * FROM users;",
  "data": [...],
  "error": null
}
```

### GET `/api/schema`
Get the database schema information.

### GET `/health`
Health check endpoint.

## Project Structure

```
text-to-sql/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Backend Docker image
│   └── .env.example        # Environment variables example
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.tsx         # Main app component
│   │   └── main.tsx        # Entry point
│   ├── package.json        # Node dependencies
│   ├── vite.config.ts      # Vite configuration
│   └── Dockerfile          # Frontend Docker image
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

## Security Considerations

- Only SELECT queries are allowed (no INSERT, UPDATE, DELETE)
- SQL injection protection through parameterized queries
- CORS configured for specific origins
- Environment variables for sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on the repository.

