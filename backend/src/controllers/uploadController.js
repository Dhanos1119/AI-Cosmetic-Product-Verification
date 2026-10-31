const path = require('path');
const fs = require('fs');

/**
 * Handle Image Upload & AI Gateway Forwarding Controller
 * Receives uploaded file from Multer, validates file size and mime type,
 * forwards file to FastAPI AI Service (:8001/api/analyze), and returns merged response.
 */
const uploadImage = async (req, res) => {
  console.log("-----------------------------------------");
  console.log("Backend Upload Gateway Request Received");
  console.log("Content-Type:", req.headers["content-type"]);
  console.log("Received file:", req.file ? req.file.originalname : "None");
  console.log("-----------------------------------------");

  // 1. Check if file was received by Multer
  if (!req.file) {
    return res.status(400).json({
      success: false,
      message: "No image file received. Expected FormData field: file"
    });
  }

  // 2. Verify file size is greater than 0
  if (!req.file.size || req.file.size <= 0) {
    if (req.file.path && fs.existsSync(req.file.path)) {
      try {
        fs.unlinkSync(req.file.path);
      } catch (err) {
        console.error("Error removing zero-byte file:", err);
      }
    }
    return res.status(400).json({
      success: false,
      message: "Uploaded file is empty or corrupted (0 bytes)."
    });
  }

  // 3. Verify file actually exists on disk
  if (!fs.existsSync(req.file.path)) {
    return res.status(500).json({
      success: false,
      message: "Failed to write uploaded file to server storage."
    });
  }

  const relativePath = path.join('uploads', req.file.filename).replace(/\\/g, '/');

  try {
    // 4. Forward uploaded image to FastAPI AI Service (:8001/api/analyze)
    const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8001/api/analyze';
    console.log(`Forwarding file to FastAPI AI Service at ${aiServiceUrl}...`);

    const fileBuffer = fs.readFileSync(req.file.path);
    const blob = new Blob([fileBuffer], { type: req.file.mimetype || 'image/jpeg' });
    const formData = new FormData();
    formData.append('file', blob, req.file.originalname);
    if (req.body && req.body.product_url) {
      formData.append('product_url', req.body.product_url);
    }

    const aiResponse = await fetch(aiServiceUrl, {
      method: 'POST',
      body: formData,
    });

    const aiData = await aiResponse.json();

    if (!aiResponse.ok || !aiData.success) {
      console.error("FastAPI AI Service Error Response:", aiData);
      return res.status(aiResponse.status || 500).json({
        success: false,
        message: aiData.message || aiData.detail || "AI Service analysis failed.",
        backendStorage: {
          filename: req.file.filename,
          fileUrl: `/${relativePath}`
        }
      });
    }

    console.log("AI Service Analysis Succeeded. DB Persisted:", aiData.db_persisted);

    // 5. Merge backend storage details into AI response
    const mergedResponse = {
      ...aiData,
      backend_storage: {
        filename: req.file.filename,
        originalName: req.file.originalname,
        mimetype: req.file.mimetype,
        size: req.file.size,
        fileUrl: `/${relativePath}`
      }
    };

    return res.status(200).json(mergedResponse);

  } catch (err) {
    console.error("Backend Gateway Exception during AI forwarding:", err);
    return res.status(502).json({
      success: false,
      message: `Unable to connect to AI Verification Service at port 8001. Details: ${err.message}`,
      backendStorage: {
        filename: req.file.filename,
        fileUrl: `/${relativePath}`
      }
    });
  }
};

module.exports = {
  uploadImage
};
