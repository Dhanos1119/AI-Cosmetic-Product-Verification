const cors = require('cors');

// Allowed origins for CORS (Desktop local, network IP, and fallback environment variables)
const defaultAllowedOrigins = [
  'http://localhost:3000',
  'http://192.168.1.27:3000',
  'http://127.0.0.1:3000',
];

const envOrigins = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(',').map((origin) => origin.trim())
  : [];

const allowedOrigins = Array.from(new Set([...defaultAllowedOrigins, ...envOrigins]));

const corsOptions = {
  origin: (origin, callback) => {
    // Allow requests with no origin (like Postman, curl, mobile apps)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin) || allowedOrigins.includes('*')) {
      return callback(null, true);
    } else {
      const error = new Error(`CORS policy error: Origin ${origin} is not allowed.`);
      error.status = 403;
      return callback(error);
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
};

module.exports = cors(corsOptions);
