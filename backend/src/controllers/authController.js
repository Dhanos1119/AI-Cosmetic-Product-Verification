/**
 * Authentication Controller
 * Proxies signup and login requests to the FastAPI AI & Database Service (:8001/api/auth)
 */

const getAiServiceBaseUrl = () => {
  const envUrl = process.env.AI_SERVICE_URL;
  if (envUrl) {
    return envUrl.replace(/\/api\/analyze\/?$/, '');
  }
  return 'http://localhost:8001';
};

/**
 * POST /api/auth/signup
 */
const signup = async (req, res) => {
  const { email, password, fullName, name } = req.body || {};

  if (!email || typeof email !== 'string' || !email.trim()) {
    return res.status(400).json({
      success: false,
      message: 'Email address is required.',
    });
  }

  if (!password || typeof password !== 'string' || password.length < 8) {
    return res.status(400).json({
      success: false,
      message: 'Password must be at least 8 characters.',
    });
  }

  const aiBaseUrl = getAiServiceBaseUrl();
  const targetUrl = `${aiBaseUrl}/api/auth/signup`;

  try {
    const aiResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.trim().toLowerCase(),
        password,
        fullName: (fullName || name || '').trim(),
      }),
    });

    const data = await aiResponse.json();

    if (!aiResponse.ok) {
      return res.status(aiResponse.status || 400).json({
        success: false,
        message: data.message || data.detail || 'Registration failed.',
      });
    }

    return res.status(201).json(data);
  } catch (err) {
    console.error('Auth Signup Gateway Exception:', err);
    return res.status(502).json({
      success: false,
      message: 'Unable to connect to authentication database service at port 8001.',
      error: err.message,
    });
  }
};

/**
 * POST /api/auth/login
 */
const login = async (req, res) => {
  const { email, password } = req.body || {};

  if (!email || typeof email !== 'string' || !email.trim()) {
    return res.status(400).json({
      success: false,
      message: 'Email address is required.',
    });
  }

  if (!password || typeof password !== 'string') {
    return res.status(400).json({
      success: false,
      message: 'Password is required.',
    });
  }

  const aiBaseUrl = getAiServiceBaseUrl();
  const targetUrl = `${aiBaseUrl}/api/auth/login`;

  try {
    const aiResponse = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.trim().toLowerCase(),
        password,
      }),
    });

    const data = await aiResponse.json();

    if (!aiResponse.ok) {
      return res.status(aiResponse.status || 401).json({
        success: false,
        message: data.message || data.detail || 'Invalid email or password.',
      });
    }

    return res.status(200).json(data);
  } catch (err) {
    console.error('Auth Login Gateway Exception:', err);
    return res.status(502).json({
      success: false,
      message: 'Unable to connect to authentication database service at port 8001.',
      error: err.message,
    });
  }
};

module.exports = {
  signup,
  login,
};
