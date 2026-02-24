# SkinCare AI - New Frontend Setup Guide

## What Changed

The frontend has been completely rebuilt with:
- ✅ React 18 + Vite (faster, modern)
- ✅ Ant Design (professional UI components)
- ✅ Capacitor (native iOS/Android support)
- ✅ Cross-platform compatibility (Web, iOS, Android)
- ✅ Clean architecture with Redux Toolkit

## Quick Start

### 1. Backend Setup (if not already running)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend will run on: http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on: http://localhost:3000

### 3. Or Use the Start Script (Windows)

```bash
.\scripts\start-new-frontend.bat
```

## First Time Usage

1. Open http://localhost:3000
2. Click "Sign up" to create an account
3. Login with your credentials
4. Start using the app!

## Features Available

### ✅ Working Now
- User registration and login
- Home dashboard
- Navigation between pages
- Shopping cart (local state)
- Profile history (local state)
- Responsive design

### 🚧 Needs Backend Running
- Skin analysis (requires backend API)
- Product recommendations (requires backend API)
- Order management (requires backend API)
- Loyalty rewards (requires backend API)

### 📱 Mobile Development

#### Setup for Android

```bash
cd frontend
npm run build
npx cap add android
npm run android
```

This will:
1. Build the web app
2. Add Android platform
3. Open Android Studio

#### Setup for iOS (Mac only)

```bash
cd frontend
npm run build
npx cap add ios
npm run ios
```

This will:
1. Build the web app
2. Add iOS platform
3. Open Xcode

## Project Structure

```
frontend/
├── src/
│   ├── pages/              # All page components
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Home.jsx
│   │   ├── Analysis.jsx
│   │   ├── Results.jsx
│   │   └── ...
│   ├── services/
│   │   ├── api.js          # Backend API calls
│   │   └── camera.js       # Camera integration
│   ├── store/
│   │   ├── index.js        # Redux store
│   │   ├── storage.js      # Cross-platform storage
│   │   └── slices/         # Redux slices
│   ├── App.jsx             # Main app with routing
│   └── main.jsx            # Entry point
├── capacitor.config.json   # Capacitor config
├── vite.config.js          # Vite config
└── package.json
```

## Environment Variables

Create `frontend/.env`:

```
VITE_API_URL=http://localhost:8000/api/v1
```

## Troubleshooting

### CORS Errors
Make sure backend is running and CORS is configured for `http://localhost:3000`

### Camera Not Working on Web
Camera uses native APIs. On web, it falls back to file picker. For full camera support, use mobile apps.

### Port Already in Use
Change port in `frontend/vite.config.js`:
```js
server: {
  port: 3001, // Change this
}
```

### Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Development Workflow

### Web Development
```bash
cd frontend
npm run dev
```
Hot reload enabled - changes appear instantly.

### Mobile Development
```bash
# After making changes
npm run build
npm run sync

# Then open in IDE
npm run android  # or npm run ios
```

## API Integration

All API calls are in `src/services/api.js`:
- Automatic token injection
- Error handling
- Base URL configuration

Example:
```javascript
import { login, analyzeImage } from '../services/api';

// Login
const response = await login(email, password);

// Analyze
const result = await analyzeImage(base64Image, questionnaire);
```

## State Management

Redux Toolkit with persistence:
- `auth` - User authentication (persisted)
- `cart` - Shopping cart (persisted)
- `analysis` - Analysis data (not persisted)

## Camera Integration

Using Capacitor Camera API:
```javascript
import { takePicture, pickImage } from '../services/camera';

// Take photo
const base64 = await takePicture();

// Pick from gallery
const base64 = await pickImage();
```

## Next Steps

1. ✅ Test registration and login
2. ✅ Verify backend connectivity
3. 🔄 Test skin analysis flow
4. 🔄 Test product recommendations
5. 📱 Build mobile apps (optional)

## Support

For issues:
1. Check browser console for errors
2. Verify backend is running
3. Check CORS configuration
4. Review API responses in Network tab

## Comparison: Old vs New

| Feature | Old (Expo) | New (Vite + Capacitor) |
|---------|-----------|------------------------|
| Build Speed | Slow | Fast ⚡ |
| Web Support | Limited | Full ✅ |
| UI Library | Custom | Ant Design ✅ |
| Bundle Size | Large | Optimized ✅ |
| Dev Experience | Good | Excellent ✅ |
| Mobile Support | Native | Native ✅ |

## Resources

- [Vite Documentation](https://vitejs.dev/)
- [Ant Design](https://ant.design/)
- [Capacitor](https://capacitorjs.com/)
- [React Router](https://reactrouter.com/)
- [Redux Toolkit](https://redux-toolkit.js.org/)
