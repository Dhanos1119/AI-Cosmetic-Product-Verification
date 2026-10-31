/**
 * Health Check Controller
 */
const getHealth = (req, res) => {
  return res.status(200).json({
    success: true,
    message: "Backend is running"
  });
};

module.exports = {
  getHealth
};
