import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
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
  getBrief: (id: string, round: number) => api.get(`/companies/${id}/pre-interview-brief?round=${round}`),
  getRejectionAnalysis: (id: string) => api.post(`/companies/${id}/rejection-analysis`),
};

export const interviewsApi = {
  list: (companyId: string) => api.get(`/companies/${companyId}/interviews/`),
  create: (companyId: string, data: any) => api.post(`/companies/${companyId}/interviews/`, data),
  get: (id: string) => api.get(`/interviews/${id}`),
};

export const matchApi = {
  analyze: (data: { jd_text: string; resume_text: string }) => api.post("/match/", data),
};

export const reviewApi = {
  analyze: (data: any) => api.post("/review/analyze", data),
};

export const prepApi = {
  generate: (data: any) => api.post("/prep/generate", data),
  getLatest: (companyId: string) => api.get(`/prep/latest/${companyId}`),
};

export const profileApi = {
  get: () => api.get("/profile/"),
  rebuild: () => api.post("/profile/rebuild"),
  summary: () => api.get("/profile/summary"),
};

export const dashboardApi = {
  stats: () => api.get("/dashboard/stats"),
  today: () => api.get("/dashboard/today"),
};
