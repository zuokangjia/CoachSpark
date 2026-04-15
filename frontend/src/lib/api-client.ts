import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

export const apiV2 = axios.create({
  baseURL: `${API_URL}/api/v2`,
  headers: { "Content-Type": "application/json" },
});

export const companiesApi = {
  list: () => api.get("/companies/"),
  get: (id: string) => api.get(`/companies/${id}`),
  create: (data: any) => api.post("/companies/", data),
  update: (id: string, data: any) => api.put(`/companies/${id}`, data),
  delete: (id: string) => api.delete(`/companies/${id}`),
  getChain: (id: string) => api.get(`/companies/${id}/interview-chain`),
  getStats: (id: string) => api.get(`/companies/${id}/stats`),
  getBrief: (id: string, round: number) => api.get(`/companies/${id}/pre-interview-brief?round_num=${round}`),
  getRejectionAnalysis: (id: string) => api.post(`/companies/${id}/rejection-analysis`),
  transitionStatus: (id: string, data: { new_status: string; offer_data?: any }) => api.post(`/companies/${id}/transition`, data),
};

export const interviewsApi = {
  list: (companyId: string) => api.get(`/companies/${companyId}/interviews/`),
  create: (companyId: string, data: any) => api.post(`/companies/${companyId}/interviews/`, data),
  get: (companyId: string, id: string) => api.get(`/companies/${companyId}/interviews/${id}`),
};

export const matchApi = {
  analyze: (data: { jd_text: string; resume_text?: string; use_stored_resume?: boolean }) => api.post("/match/", data),
};

export const reviewApi = {
  analyze: (data: any) => apiV2.post("/review/analyze", data),
};

export const prepApi = {
  generate: (data: any) => api.post("/prep/generate", data),
  getLatest: (companyId: string) => api.get(`/prep/latest/${companyId}`),
  updateTaskCompletion: (
    prepPlanId: string,
    data: { day: number; task_index: number; completed: boolean },
  ) => api.patch(`/prep/${prepPlanId}/task`, data),
};

export const profileApi = {
  get: () => apiV2.get("/persona/latest"),
  rebuild: () => api.post("/profile/rebuild"),
  summary: () => apiV2.get("/persona/latest"),
  persona: () => apiV2.get("/persona/latest"),
};

export const personaV2Api = {
  latest: () => apiV2.get("/persona/latest"),
  rebuild: () => apiV2.post("/persona/rebuild"),
  explain: (dimension: string, limit = 10) => apiV2.get(`/persona/explain?dimension=${encodeURIComponent(dimension)}&limit=${limit}`),
  snapshots: (limit = 20) => apiV2.get(`/persona/snapshots?limit=${limit}`),
  compare: (baseSnapshotId: string, targetSnapshotId: string) =>
    apiV2.get(`/persona/compare?base_snapshot_id=${encodeURIComponent(baseSnapshotId)}&target_snapshot_id=${encodeURIComponent(targetSnapshotId)}`),
};

export const dashboardApi = {
  stats: () => api.get("/dashboard/stats"),
  today: () => api.get("/dashboard/today"),
};

export const offersApi = {
  list: () => api.get("/offers/"),
  create: (data: any) => api.post("/offers/", data),
  update: (id: string, data: any) => api.put(`/offers/${id}`, data),
  delete: (id: string) => api.delete(`/offers/${id}`),
};

export const resumeApi = {
  get: () => api.get("/resume/"),
  update: (data: any) => api.put("/resume/", data),
  rebuild: () => api.post("/resume/rebuild"),
};

export const practiceApi = {
  list: (queryString?: string) =>
    apiV2.get(`/practice/questions${queryString ? `?${queryString}` : ""}`),
  get: (id: string) => apiV2.get(`/practice/questions/${id}`),
  submit: (id: string, data: { submitted_answer: string; time_spent_seconds?: number }) =>
    apiV2.post(`/practice/questions/${id}/submit`, data),
  history: (limit = 20, offset = 0) =>
    apiV2.get(`/practice/history?limit=${limit}&offset=${offset}`),
  recommend: (limit = 5) =>
    apiV2.get(`/practice/recommend?limit=${limit}`),
  categories: () => apiV2.get("/practice/categories"),
  importText: (data: { text: string; category_name?: string }) =>
    apiV2.post("/practice/import-text", data),
  generateDrill: (data: { topic: string; num_questions?: number }) =>
    apiV2.post("/practice/generate", data),
};
