/**
 * TruthLens Mobile API Client
 * All communication with the TruthLens backend.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const DEFAULT_API_URL = 'http://localhost:8000';

export async function getApiUrl() {
  return (await AsyncStorage.getItem('apiUrl')) || DEFAULT_API_URL;
}

export async function setApiUrl(url) {
  await AsyncStorage.setItem('apiUrl', url);
}

export async function analyzeText(text) {
  const url = await getApiUrl();
  const resp = await fetch(`${url}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `text=${encodeURIComponent(text)}`,
  });
  return resp.json();
}

export async function analyzeImage(imageUri) {
  const url = await getApiUrl();
  const formData = new FormData();
  formData.append('image', { uri: imageUri, type: 'image/jpeg', name: 'photo.jpg' });
  const resp = await fetch(`${url}/analyze`, { method: 'POST', body: formData });
  return resp.json();
}

export async function getHistory(limit = 20) {
  const url = await getApiUrl();
  const resp = await fetch(`${url}/analyses?limit=${limit}`);
  return resp.json();
}

export async function getInvestigation(analysisId) {
  const url = await getApiUrl();
  const resp = await fetch(`${url}/investigations/${analysisId}`);
  return resp.json();
}

export async function healthCheck() {
  const url = await getApiUrl();
  const resp = await fetch(`${url}/health`);
  return resp.json();
}
