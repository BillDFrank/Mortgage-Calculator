# Mortgage Calculator with EURIBOR Integration

A modern mortgage calculator application with EURIBOR rate integration, built with Next.js frontend and Python FastAPI backend.

## Features

- Calculate mortgage payments with various parameters
- EURIBOR rate integration for accurate calculations
- Amortization schedule visualization
- Historical EURIBOR rate charts
- Responsive design for all devices
- Dark/light mode support

## Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Next.js       │    │   Python         │
│   Frontend      │◄──►│   FastAPI        │
│                 │    │   Backend        │
└─────────────────┘    └──────────────────┘
       │                        │
       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   Docker        │    │   Docker         │
│   Container     │    │   Container      │
└─────────────────┘    └──────────────────┘
```

## Tech Stack

### Frontend
- Next.js 14 with TypeScript
- Tailwind CSS for styling
- Chart.js for data visualization
- Axios for API requests

### Backend
- Python FastAPI
- Uvicorn ASGI server
- Pandas for data processing

### Deployment
- Docker & Docker Compose
- GitHub Actions for CI/CD

## Prerequisites

- Node.js 18+
- Python 3.9+
- Docker (optional, for containerized deployment)
- Docker Compose (optional, for containerized deployment)

## Quick Start

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd mortgage-calculator
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
```bash
cd ../backend
pip install -r requirements.txt
```

4. Start the development servers:

Backend:
```bash
cd backend
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

### Docker Setup

1. Build and start services:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

## API Endpoints

### EURIBOR Rates
- `GET /api/euribor/latest?tenor={tenor}` - Get latest EURIBOR rate
- `GET /api/euribor/history?tenor={tenor}&from_date={from}&to_date={to}` - Get historical EURIBOR rates

### Mortgage Calculation
- `POST /api/calc` - Calculate mortgage details

## Project Structure

```
mortgage-calculator/
├── backend/
│   ├── api/
│   │   ├── euribor.py
│   │   ├── calculator.py
│   │   └── routes.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Development

### Backend Development

The backend is built with Python FastAPI and provides RESTful API endpoints for mortgage calculations and EURIBOR data.

### Frontend Development

The frontend is built with Next.js 14 and TypeScript, providing a responsive and user-friendly interface.

## Deployment

The application can be deployed using Docker Compose to any cloud platform that supports containerized applications.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- EURIBOR data provided by the European Central Bank
- Built with Next.js, FastAPI, and Docker