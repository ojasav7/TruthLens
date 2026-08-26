# TruthLens Mobile App

React Native app for on-the-go misinformation detection.

## Setup

```bash
cd mobile
npx react-native init TruthLensMobile
# Copy the files from this directory into the project
npm install @react-navigation/native @react-navigation/stack
npm install react-native-image-picker
```

## API Client

All API calls go through `src/api.js` which points to the TruthLens backend.

## Screens

| Screen | Purpose |
|--------|---------|
| Home | Text input + image upload |
| Results | Threat score, verdict, breakdown |
| History | Past analyses |
| Settings | API URL configuration |
