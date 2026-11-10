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

      // Handle Expired or Invalid Authentication
      if (response.status === 401) {
        const hadToken = !!localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN);
        if (hadToken) {
          localStorage.removeItem(CONFIG.STORAGE_KEYS.TOKEN);
          localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
          window.dispatchEvent(new CustomEvent("sg:auth-expired", {
            detail: { message: errorMsg }
          }));
        }
      }

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
      // Network unreachable fallback
      if (!err.status && err.name === "TypeError") {
        const netErr = new Error("Unable to connect to SkillGraph backend server at " + CONFIG.API_BASE_URL);
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
        window.dispatchEvent(new CustomEvent("sg:auth-changed"));
      },
      isAuthenticated: () => !!localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN),
      requireAuth: (redirectTarget) => {
        if (!localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN)) {
          const current = redirectTarget || window.location.pathname.split("/").pop() || "dashboard.html";
          window.location.href = `auth.html?redirect=${encodeURIComponent(current)}`;
          return false;
        }
        return true;
      },
      getUser: () => {
        try {
          return JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.USER) || "null");
        } catch {
          return null;
        }
      }
    },

    // 2.5 User Profile & Onboarding
    user: {
      getOnboarding: () => request("/api/user/onboarding", { method: "GET" }),
      saveOnboarding: (data) => request("/api/user/onboarding", {
        method: "POST",
        body: JSON.stringify(data)
      }),
      updateProfile: (data) => request("/api/user/profile", {
        method: "PUT",
        body: JSON.stringify(data)
      })
    },

    // 3. Roles & Taxonomy
    roles: {
      list: async (params = {}) => {
        const query = new URLSearchParams(params).toString();
        const url = query ? `/api/roles/?${query}` : "/api/roles/";
        const res = await request(url, { method: "GET" });
        return Array.isArray(res) ? res : (res && res.roles) ? res.roles : [];
      },
      get: (roleId) => request(`/api/roles/${encodeURIComponent(roleId)}`, { method: "GET" }),
      getRelated: (roleId, topN = 4) => request(`/api/roles/${encodeURIComponent(roleId)}/related?top_n=${topN}`, { method: "GET" }),
      compare: (roleA, roleB, userSkills = null) => {
        let url = `/api/roles/compare?role_a=${encodeURIComponent(roleA)}&role_b=${encodeURIComponent(roleB)}`;
        if (userSkills) {
          const skillsStr = Array.isArray(userSkills) ? userSkills.join(",") : userSkills;
          url += `&user_skills=${encodeURIComponent(skillsStr)}`;
        }
        return request(url, { method: "GET" });
      },
      getMarketSummary: (roleId) => request(`/api/roles/${encodeURIComponent(roleId)}/market-summary`, { method: "GET" })
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
      critique: (payload) => request("/api/resume/critique", {
        method: "POST",
        body: JSON.stringify(payload)
      }),
      listRecords: () => request("/api/resume/records", { method: "GET" }),
      getRecord: (id) => request(`/api/resume/records/${id}`, { method: "GET" }),
      deleteRecord: (id) => request(`/api/resume/records/${id}`, { method: "DELETE" }),
      updateSkills: (skills, recordId = null) => {
        const url = recordId ? `/api/resume/records/${recordId}/skills` : "/api/resume/skills";
        return request(url, {
          method: "PUT",
          body: JSON.stringify({ skills })
        });
      }
    },

    // 5. Skills & Gap Analysis
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
      listAnalyses: () => request("/api/job-descriptions/analyses", { method: "GET" }),
      getMarketTrends: (family = null) => {
        const query = family ? `?family=${encodeURIComponent(family)}` : "";
        return request(`/api/job-descriptions/market-trends${query}`, { method: "GET" });
      }
    },

    // 7. Coding Profiles (GitHub + LeetCode)
    profiles: {
      analyze: (handles) => request("/api/profiles/analyze", {
        method: "POST",
        body: JSON.stringify(handles)
      }),
      getSaved: () => request("/api/profiles/saved", { method: "GET" }),
      getMe: () => request("/api/profiles/me", { method: "GET" })
    },

    // 7. Roadmaps & Progress
    roadmaps: {
      generate: (params) => request("/api/roadmaps/generate", {
        method: "POST",
        body: JSON.stringify(params)
      }),
      list: () => request("/api/roadmaps", { method: "GET" }),
      listSaved: () => request("/api/roadmaps", { method: "GET" }),
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

    get roadmap() {
      return this.roadmaps;
    },

    progress: {
      get: () => request("/api/progress", { method: "GET" })
    }
  };
})();
