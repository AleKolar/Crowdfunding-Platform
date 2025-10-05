# Crowdfunding Platform 

![CI](https://github.com/AleKolar/Crowdfunding-Platform/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/AleKolar/Crowdfunding-Platform/actions/workflows/cd.yml/badge.svg)
![Coverage](https://img.shields.io/badge/Coverage-Testing-blue)

A modern crowdfunding platform built with FastAPI, PostgreSQL, and Redis.

## 🚀 Features

- User authentication with 2FA
- Project creation and management  
- Secure payment processing with Stripe
- Real-time notifications
- Media uploads for projects
- RESTful API with OpenAPI documentation

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL, SQLAlchemy
- **Cache**: Redis
- **Authentication**: JWT, bcrypt
- **Payments**: Stripe
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Testing**: Pytest, Coverage

## 📦 Development

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/AleKolar/Crowdfunding-Platform.git
cd Crowdfunding-Platform

# Start with Docker Compose
docker-compose up --build

# The application will be available at:
# API: http://localhost:8000
# Docs: http://localhost:8000/docs