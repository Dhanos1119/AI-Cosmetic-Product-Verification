/**
 * Direct Marketplace URL Scraping Controller
 * Proxies user-submitted marketplace URL to FastAPI AI Service (:8001/api/marketplace/scrape-url)
 */
const scrapeUrl = async (req, res) => {
  const { url, platform } = req.body || {};

  if (!url || typeof url !== 'string' || !url.trim()) {
    return res.status(400).json({
      success: false,
      message: 'Missing or invalid required field: url',
    });
  }

  const aiBaseUrl = process.env.AI_SERVICE_URL
    ? process.env.AI_SERVICE_URL.replace(/\/api\/analyze\/?$/, '')
    : 'http://localhost:8001';
  const targetUrl = `${aiBaseUrl}/api/marketplace/scrape-url`;

  try {
    const aiResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url.trim(),
        platform: platform || undefined,
      }),
    });

    const data = await aiResponse.json();

    if (!aiResponse.ok) {
      return res.status(aiResponse.status || 500).json({
        success: false,
        message: data.message || data.detail || 'Marketplace URL extraction failed on AI Service.',
      });
    }

    return res.status(200).json(data);
  } catch (err) {
    console.error('Marketplace URL Gateway Exception:', err);
    return res.status(502).json({
      success: false,
      message: 'Failed to connect to FastAPI AI Service at port 8001.',
      error: err.message,
    });
  }
};

module.exports = { scrapeUrl };
