# Frontend - Smart Triage Kiosk System

Progressive Web Application (PWA) built with React 18, TypeScript, and Material-UI for the Smart Triage Kiosk System.

## Features

- **Offline-First Architecture** - Complete functionality without internet
- **Multilingual Support** - English, Hindi, and local languages
- **Voice Interface** - Speech-to-text and text-to-speech capabilities
- **Accessibility** - WCAG 2.1 AA compliant with high contrast and large text
- **Device Integration** - Bluetooth medical device connectivity
- **Real-time Updates** - WebSocket integration for queue management
- **Touch-Optimized** - Designed for kiosk touch screens

## Tech Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **Redux Toolkit** for state management
- **React Hook Form** for form handling
- **React Query** for API data management
- **PWA** with service workers for offline support
- **Web Bluetooth API** for device integration
- **Web Speech API** for voice features
- **React-i18next** for internationalization

## Setup

```bash
npm install
npm start
```

## Build

```bash
npm run build
npm run serve
```

## Project Structure

```
src/
├── components/        # Reusable UI components
├── features/          # Feature-specific components
├── hooks/            # Custom React hooks
├── i18n/             # Internationalization files
├── pages/            # Page components
├── redux/            # Redux store and slices
├── services/         # API and external services
├── styles/           # Global styles and themes
├── utils/            # Utility functions
└── types/            # TypeScript type definitions
```

## Environment Variables

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
```
