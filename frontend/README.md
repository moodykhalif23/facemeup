# SkinCare AI Frontend

Modern, cross-platform frontend built with React, Ant Design, and Capacitor.

## Tech Stack

- **React 18** - UI library
- **Ant Design** - UI component library
- **Vite** - Build tool and dev server
- **React Router** - Routing
- **Redux Toolkit** - State management
- **Capacitor** - Native mobile capabilities
- **Axios** - HTTP client

## Features

- ✅ Cross-platform (Web, iOS, Android)
- ✅ AI-powered skin analysis
- ✅ Camera integration
- ✅ Product recommendations
- ✅ Shopping cart
- ✅ Order tracking
- ✅ Loyalty rewards
- ✅ Offline support with local storage

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- For iOS: Xcode (Mac only)
- For Android: Android Studio

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

### Development

```bash
# Run web development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Mobile Development

#### First Time Setup

```bash
# Add iOS platform (Mac only)
npx cap add ios

# Add Android platform
npx cap add android
```

#### Running on Mobile

```bash
# Sync web assets to native projects
npm run sync

# Open in Android Studio
npm run android

# Open in Xcode (Mac only)
npm run ios
```
## Building for Production

### Web

```bash
npm run build
# Output in dist/
```

### Android

1. Run `npm run build`
2. Run `npm run sync`
3. Open Android Studio: `npm run android`
4. Build APK/Bundle from Android Studio

### iOS

1. Run `npm run build`
2. Run `npm run sync`
3. Open Xcode: `npm run ios`
4. Build from Xcode

## Capacitor Plugins Used

- `@capacitor/camera` - Camera and photo library access
- `@capacitor/preferences` - Local storage
- `@capacitor/network` - Network status
- `@capacitor/app` - App lifecycle

## State Management

Redux Toolkit with persistence:
- `auth` - Authentication state
- `analysis` - Skin analysis data
- `cart` - Shopping cart items

## API Integration

All API calls are in `src/services/api.js` with automatic token injection.

## Troubleshooting

### Camera not working on web
The camera uses native APIs. On web, it falls back to file picker.

### Build errors
```bash
rm -rf node_modules package-lock.json
npm install
```

### Capacitor sync issues
```bash
npx cap sync
```
