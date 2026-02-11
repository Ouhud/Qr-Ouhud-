// Basic Service Worker for Ouhud QR
self.addEventListener('install', event => {
  console.log('Service worker installing...');
  // Skip waiting to activate immediately
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  console.log('Service worker activating...');
  // Claim all clients
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  // For now, just pass through all requests
  event.respondWith(fetch(event.request));
});
