# SkinCare AI Frontend

Modern, cross-platform frontend built with React, Ant Design, and Capacitor.

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
npx cap add ios
npx cap add android
```

#### Running on Mobile

```bash
npm run sync
npm run android
npm run ios
```
## Building for Production

### Web

```bash
npm run build
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
npx cap doctor
```
