# SkinCare AI

AI-powered skincare analysis and personalized product recommendation platform with e-commerce, loyalty rewards, and progress tracking.

## 🚀 Quick Start

### Option 1: Docker + New Frontend (Recommended)

**Windows:**
```bash
# Setup (first time only)
.\scripts\setup-docker.bat

# Start development
.\scripts\start-new-frontend.bat
```

**Mac/Linux:**
```bash
# Setup (first time only)
chmod +x scripts/setup-docker.sh
./scripts/setup-docker.sh

# Start development
chmod +x scripts/start-new-frontend.sh
./scripts/start-new-frontend.sh
```

This will:
1. Start backend services (Docker)
2. Run database migrations
3. Start the new React frontend

### Option 2: Manual Setup

1. **Backend (Docker):**
   ```bash
   docker-compose up -d
   docker-compose exec api alembic upgrade head
   ```

2. **Frontend (New React + Vite):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🌐 Access Points

Once started:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## ✨ Features

### Core Features
- 🤖 AI-powered skin analysis with camera integration
- 💡 Personalized product recommendations
- 📋 Multi-step questionnaire for accurate analysis
- 🛒 E-commerce with retail/wholesale pricing
- 🎁 Loyalty points and rewards system
- 📸 Progress photo tracking with before/after comparison
- 🔐 User authentication (JWT)
- 📊 Profile history tracking

## 🛠 Technology Stack

### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Cache:** Redis
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Auth:** JWT (python-jose)
- **ML:** TensorFlow/Keras (EfficientNetB0)

### Frontend (New - React + Capacitor)
- **Framework:** React 18
- **Build Tool:** Vite
- **UI Library:** Ant Design
- **State Management:** Redux Toolkit
- **Routing:** React Router v6
- **Mobile:** Capacitor (iOS/Android)
- **API Client:** Axios
- **Storage:** Capacitor Preferences / LocalStorage

### Frontend (Legacy - Expo)
- **Framework:** React Native (Expo)
- **State Management:** Redux Toolkit
- **UI Library:** Ant Design React Native
- **Navigation:** React Navigation

## 📱 Mobile Development (New Frontend)

### Android
```bash
cd frontend
npm run build
npx cap add android
npm run android
```

### iOS (Mac only)
```bash
cd frontend
npm run build
npx cap add ios
npm run ios
```

## 🔧 Development

### Backend Development

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# View logs
docker-compose logs -f api

# Access container shell
docker-compose exec api bash

# Run tests
docker-compose exec api pytest
```

### Frontend Development (New)

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Sync with mobile platforms
npm run sync
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

- [New Frontend Setup Guide](SETUP_NEW_FRONTEND.md) ⭐ **Start here!**
- [Implementation Gap Analysis](docs/IMPLEMENTATION_GAP_ANALYSIS.md)
- [ML Pipeline Setup](docs/ML_PIPELINE_SETUP.md)
- [Frontend README](frontend/README.md)
- [Backend README](backend/README.md)

## 🧪 Testing

### Backend Tests
```bash
docker-compose exec api pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🐛 Troubleshooting

### Database Not Initialized
```bash
# Run migrations
docker-compose exec api alembic upgrade head
```

### CORS Errors
- Ensure backend allows `http://localhost:3000`
- Check `backend/app/main.py` CORS configuration

### Docker Issues
- Ensure Docker Desktop is running
- Check port availability (8000, 5432, 6379, 3000)
- Reset: `docker-compose down -v && docker-compose up -d`

### Frontend Issues (New)
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:3000 | xargs kill -9
```

## 🗂 Project Structure

```
skincare/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core functionality
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── ml/              # ML pipeline
│   └── tests/           # Backend tests
├── frontend/            # React frontend (NEW)
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── services/    # API & native services
│   │   └── store/       # Redux store
│   └── capacitor.config.json
├── docs/                # Documentation
└── scripts/             # Setup scripts
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

