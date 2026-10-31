const express = require('express');
const router = express.Router();
const upload = require('../middleware/uploadMiddleware');
const { uploadImage } = require('../controllers/uploadController');

// Accept single image file strictly with field name "file"
const uploadSingleFile = upload.single('file');

// POST /api/upload
router.post('/', uploadSingleFile, uploadImage);

module.exports = router;
