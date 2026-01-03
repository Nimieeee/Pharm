
// Centralized API Configuration
// Production uses relative paths to leverage Vercel rewrites (proxies)
// Local uses the dedicated development port

export const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? '' // Relative path for Vercel Rewrites proxy
    : 'http://localhost:8000';

export const UPLOAD_BASE_URL = 'https://35-181-4-139.sslip.io';
