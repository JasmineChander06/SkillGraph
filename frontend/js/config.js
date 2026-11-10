/**
 * SkillGraph Client Configuration
 * Edition: "Paper & Ink"
 */

const CONFIG = {
  // Backend API URL (defaulting to local development server)
  API_BASE_URL: (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? (window.location.port === "8000" ? window.location.origin : "http://127.0.0.1:8000")
    : (window.location.origin),

  // Storage Keys
  STORAGE_KEYS: {
    TOKEN: "sg_token",
    USER: "sg_user",
    ACTIVE_ROLE: "sg_active_role",
    LATEST_ROADMAP_ID: "sg_latest_roadmap_id"
  },

  // Default target role list if offline (metadata only, no fake readiness scores)
  DEFAULT_ROLES: [
    { id: "harness-engineer", title: "Harness Engineer" },
    { id: "backend-engineer", title: "Backend Engineer" },
    { id: "machine-learning-engineer", title: "Machine Learning Engineer" },
    { id: "data-engineer", title: "Data Engineer" },
    { id: "llmops-engineer", title: "LLMOps Engineer" }
  ]
};

// Freeze config object to prevent accidental mutation
Object.freeze(CONFIG);
Object.freeze(CONFIG.STORAGE_KEYS);

