const express = require('express');
const router = express.Router();
const { scrapeUrl } = require('../controllers/marketplaceController');

// POST /api/marketplace/scrape-url
router.post('/scrape-url', scrapeUrl);

module.exports = router;
