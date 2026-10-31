const multer = require('multer');

/**
 * Global Error Handler Middleware
 */
const errorHandler = (err, req, res, next) => {
  // Handle Multer specific errors (Status 400)
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        message: 'File size exceeds the 10 MB limit.'
      });
    }
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      return res.status(400).json({
        success: false,
        message: 'Unexpected file field. Please upload using field name "file".'
      });
    }
    return res.status(400).json({
      success: false,
      message: `Upload error: ${err.message}`
    });
  }

  // Handle custom file type validation error (Status 400)
  if (err.code === 'INVALID_FILE_TYPE') {
    return res.status(400).json({
      success: false,
      message: err.message
    });
  }

  // Handle CORS policy errors (Status 403)
  if (err.status === 403) {
    return res.status(403).json({
      success: false,
      message: err.message
    });
  }

  // Handle generic server errors (Status 500)
  console.error('Server Error:', err);
  return res.status(err.status || 500).json({
    success: false,
    message: err.message || 'Internal Server Error'
  });
};

module.exports = errorHandler;
