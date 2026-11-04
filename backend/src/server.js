const path = require('path');
const dotenv = require('dotenv');

// Load environment variables from .env file
dotenv.config({ path: path.join(__dirname, '../.env') });

const express = require('express');
const corsMiddleware = require('./config/corsConfig');
const healthRoutes = require('./routes/healthRoutes');
const uploadRoutes = require('./routes/uploadRoutes');
const marketplaceRoutes = require('./routes/marketplaceRoutes');
const authRoutes = require('./routes/authRoutes');
const errorHandler = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS
app.use(corsMiddleware);

// Middleware for parsing JSON and URL-encoded form data
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve uploaded static files from /uploads directory
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// API Routes
app.use('/api/health', healthRoutes);
app.use('/api/upload', uploadRoutes);
app.use('/api/marketplace', marketplaceRoutes);
app.use('/api/auth', authRoutes);

// Root route handler
app.get('/', (req, res) => {
  res.status(200).json({
    success: true,
    message: "Welcome to CosmeticVerify API Server",
    endpoints: {
      health: "/api/health",
      upload: "/api/upload (POST)",
      marketplace: "/api/marketplace/scrape-url (POST)",
      auth: {
        signup: "/api/auth/signup (POST)",
        login: "/api/auth/login (POST)"
      }
    }
  });
});

// 404 Route Handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: `Endpoint ${req.originalUrl} not found`
  });
});

// Global Error Handler Middleware
app.use(errorHandler);

// Start Server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`===========================================`);
  console.log(`🚀 CosmeticVerify Backend Server Running`);
  console.log(`📡 Local:   http://localhost:${PORT}`);
  console.log(`📡 Network: http://192.168.1.27:${PORT}`);
  console.log(`===========================================`);
});
