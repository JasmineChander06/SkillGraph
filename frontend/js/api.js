/**
 * SkillGraph REST API Client
 * Vanilla JavaScript (Zero Frameworks, Native Fetch)
 */

const API = (() => {
  const getHeaders = (isFormData = false) => {
    const headers = {};
    if (!isFormData) {
      headers["Content-Type"] = "application/json";
    }
    const token = localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN);
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  };

  const handleResponse = async (response) => {
    const contentType = response.headers.get("content-type");
    let data = null;

    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      const errorMsg = (data && data.detail)
        ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
        : `Request failed with status ${response.status}`;
      const error = new Error(errorMsg);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  };

  const request = async (path, options = {}) => {
    const url = `${CONFIG.API_BASE_URL}${path}`;
    const isFormData = options.body instanceof FormData;
    const fetchOptions = {
      ...options,
      headers: {
        ...getHeaders(isFormData),
        ...(options.headers || {})
      }
    };

    try {
      const response = await fetch(url, fetchOptions);
      return await handleResponse(response);
    } catch (err) {
      // Re-throw with helpful message if network completely failed
      if (!err.status && err.name === "TypeError") {
        const netErr = new Error("Unable to connect to SkillGraph backend server.");
        netErr.status = 0;
        throw netErr;
      }
      throw err;
    }
  };

  return {
    // 1. Health & Status
    health: {
      check: () => request("/api/health", { method: "GET" })
    },

    // 2. Authentication
    auth: {
      register: (userData) => request("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(userData)
      }),
      login: (credentials) => request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials)
      }),
      getMe: () => request("/api/auth/me", { method: "GET" }),
      logout: () => {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.TOKEN);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
      },
      isAuthenticated: () => !!localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN),
      getUser: () => {
        try {
          return JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.USER) || "null");
        } catch {
          return null;
        }
      }
    },

    // 3. Roles
    roles: {
      list: () => request("/api/roles/", { method: "GET" }),
      get: (roleId) => request(`/api/roles/${encodeURIComponent(roleId)}`, { method: "GET" })
    },

    // 4. Resume
    resume: {
      parse: (file) => {
        const formData = new FormData();
        formData.append("file", file);
        return request("/api/resume/parse", {
          method: "POST",
          body: formData
        });
      },
      listRecords: () => request("/api/resume/records", { method: "GET" }),
      getRecord: (id) => request(`/api/resume/records/${id}`, { method: "GET" }),
      deleteRecord: (id) => request(`/api/resume/records/${id}`, { method: "DELETE" })
    },

    // 5. Skills & Analysis
    skills: {
      analyze: (text, roleId) => request("/api/skills/analyze", {
        method: "POST",
        body: JSON.stringify({ text, role_id: roleId })
      }),
      listAnalyses: () => request("/api/skills/analyses", { method: "GET" }),
      getAnalysis: (id) => request(`/api/skills/analyses/${id}`, { method: "GET" })
    },

    // 6. Job Descriptions
    jobs: {
      analyze: (resumeText, jobDescriptionText) => request("/api/job-descriptions/analyze", {
        method: "POST",
        body: JSON.stringify({
          resume_text: resumeText,
          job_description_text: jobDescriptionText
        })
      }),
      listAnalyses: () => request("/api/job-descriptions/analyses", { method: "GET" })
    },

    // 7. Roadmaps & Progress
    roadmaps: {
      generate: (params) => request("/api/roadmaps/generate", {
        method: "POST",
        body: JSON.stringify(params)
      }),
      list: () => request("/api/roadmaps", { method: "GET" }),
      get: (id) => request(`/api/roadmaps/${id}`, { method: "GET" }),
      delete: (id) => request(`/api/roadmaps/${id}`, { method: "DELETE" }),
      updateTask: (roadmapId, taskId, status, notes = null) => {
        const url = roadmapId
          ? `/api/roadmaps/${roadmapId}/tasks/${taskId}`
          : `/api/roadmaps/tasks/${taskId}`;
        return request(url, {
          method: "PATCH",
          body: JSON.stringify({ status, notes })
        });
      }
    },

    progress: {
      get: () => request("/api/progress", { method: "GET" })
    }
  };
})();

