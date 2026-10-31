const multer = require('multer');
const path = require('path');
const fs = require('fs');

// Ensure uploads directory exists
const uploadDir = path.join(__dirname, '../../uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

// Configure Storage Engine for original binary images
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    const ext = path.extname(file.originalname).toLowerCase();
    const nameWithoutExt = path
      .basename(file.originalname, ext)
      .replace(/[^a-zA-Z0-9]/g, '_');
    cb(null, `${nameWithoutExt}-${uniqueSuffix}${ext}`);
  },
});

// Allowed image MIME types and extensions
const allowedMimeTypes = ['image/jpeg', 'image/jpg', 'image/png'];
const allowedExtensions = ['.jpg', '.jpeg', '.png'];

const fileFilter = (req, file, cb) => {
  const ext = path.extname(file.originalname).toLowerCase();
  const mime = file.mimetype.toLowerCase();

  if (allowedMimeTypes.includes(mime) && allowedExtensions.includes(ext)) {
    cb(null, true);
  } else {
    const error = new Error('Invalid file type. Only JPG, JPEG, and PNG files are allowed.');
    error.code = 'INVALID_FILE_TYPE';
    cb(error, false);
  }
};

// Multer Instance configured for field name "file"
const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10 MB limit
  },
});

module.exports = upload;
