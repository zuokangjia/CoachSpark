import { create } from "zustand";

export interface Company {
  id: string;
  name: string;
  position: string;
  status: string;
  applied_date: string | null;
  next_event_date: string | null;
  next_event_type: string | null;
  notes: string | null;
  jd_text: string | null;
  created_at: string;
  updated_at: string;
}

interface CompanyState {
  companies: Company[];
  loading: boolean;
  fetchCompanies: () => Promise<void>;
  addCompany: (company: Company) => void;
  updateCompany: (id: string, updates: Partial<Company>) => void;
  removeCompany: (id: string) => void;
  moveCompany: (id: string, newStatus: string) => void;
}

export const useCompanyStore = create<CompanyState>((set) => ({
  companies: [],
  loading: false,
  fetchCompanies: async () => {
    set({ loading: true });
    try {
      const { companiesApi } = await import("@/lib/api-client");
      const res = await companiesApi.list();
      set({ companies: res.data, loading: false });
    } catch {
      set({ loading: false });
    }
  },
  addCompany: (company) => set((state) => ({ companies: [...state.companies, company] })),
  updateCompany: (id, updates) =>
    set((state) => ({
      companies: state.companies.map((c) => (c.id === id ? { ...c, ...updates } : c)),
    })),
  removeCompany: (id) =>
    set((state) => ({
      companies: state.companies.filter((c) => c.id !== id),
    })),
  moveCompany: (id, newStatus) =>
    set((state) => ({
      companies: state.companies.map((c) => (c.id === id ? { ...c, status: newStatus } : c)),
    })),
}));
