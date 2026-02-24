# SkinCare AI

AI-powered skincare analysis and personalized product recommendation platform with e-commerce, loyalty rewards, and progress tracking.

## Quick Start

### Automated Setup (Recommended)

**Windows:**
```bash
scripts\start-dev.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

This will automatically:
1. Start backend services (Docker)
2. Install frontend dependencies
3. Launch the development server

### Manual Setup

1. **Backend:**
   ```bash
   cd backend
   docker-compose up --build
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm install
   npm start
   ```

##  Features

### Core Features
- AI-powered skin analysis with camera integration
- Personalized product recommendations
- Multi-step questionnaire for accurate analysis
- E-commerce with retail/wholesale pricing
- Loyalty points and rewards system
- Progress photo tracking with before/after comparison
- User authentication (JWT)
- Profile history tracking

##  Technology Stack

### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Cache:** Redis
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Auth:** JWT (python-jose)
- **ML:** TensorFlow/Keras (EfficientNetB0)

### Frontend
- **Framework:** React Native (Expo)
- **State Management:** Redux Toolkit
- **UI Library:** Ant Design React Native
- **Navigation:** React Navigation
- **API Client:** RTK Query
- **Storage:** AsyncStorage
- **Network:** NetInfo

## Services

Once started, access:

- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Frontend (Expo):** http://localhost:8081
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## Development

### Backend Development

```bash
cd backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# View logs
docker-compose logs -f backend

# Run tests
docker-compose exec backend pytest
```

### Frontend Development

```bash
cd frontend
npm install
npm start

# Run on specific platform
npm run android  # Android
npm run ios      # iOS
npm run web      # Web browser

# Run tests
npm test
```

### ML Pipeline

```bash
cd backend/ml

# Install dependencies
pip install -r ../requirements.txt

# Download ISIC dataset
python scripts/download_isic.py

# Train model
python train.py

# Evaluate model
python evaluate.py

# Export to TFLite
python export_tflite.py
```

## 📚 Documentation

- [Implementation Gap Analysis](docs/IMPLEMENTATION_GAP_ANALYSIS.md)
- [ML Pipeline Setup](docs/ML_PIPELINE_SETUP.md)

## 🧪 Testing

### Backend Tests
```bash
cd backend
docker-compose exec backend pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request


## Troubleshooting

### Docker Issues
- Ensure Docker Desktop is running
- Check port availability (8000, 5432, 6379, 8081)
- Try `docker-compose down -v` to reset volumes

### Frontend Issues
- Delete `node_modules` and run `npm install` again
- Clear Expo cache: `expo start -c`
- Check Node.js version (requires v18+)

### Backend Issues
- Check Docker logs: `docker-compose logs backend`
- Verify database connection
- Ensure migrations are up to date

