import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";
export const API = `${BACKEND_URL}/api`;
export const FILE_BASE = BACKEND_URL;

export const api = axios.create({ baseURL: API });

export const endpoints = {
  login: (employee_id) => api.post("/auth/login", { employee_id }),
  users: () => api.get("/users"),
  createUser: (data) => api.post("/users", data),
  deleteUser: (id) => api.delete(`/users/${id}`),
  meta: () => api.get("/meta"),
  tickets: (params) => api.get("/tickets", { params }),
  createTicket: (data) => api.post("/tickets", data),
  updateTicket: (id, data) => api.patch(`/tickets/${id}`, data),
  inventory: () => api.get("/inventory"),
  createItem: (data) => api.post("/inventory", data),
  updateItem: (id, data) => api.patch(`/inventory/${id}`, data),
  deleteItem: (id) => api.delete(`/inventory/${id}`),
  reminders: () => api.get("/reminders"),
  createReminder: (data) => api.post("/reminders", data),
  toggleReminder: (id) => api.patch(`/reminders/${id}`),
  deleteReminder: (id) => api.delete(`/reminders/${id}`),
  logs: () => api.get("/logs"),
  stats: () => api.get("/stats"),
  assets: () => api.get("/assets"),
  createAsset: (data) => api.post("/assets", data),
  updateAsset: (id, data) => api.patch(`/assets/${id}`, data),
  deleteAsset: (id) => api.delete(`/assets/${id}`),
  exportAssets: () => api.get("/assets/export", { responseType: "blob" }),
  setupNeeded: () => api.get("/setup-needed"),
  setup: (data) => api.post("/setup", data),
  uploadFile: (formData) => api.post("/upload", formData),
  importInventory: (formData) => api.post("/inventory/import", formData),
  inventoryTemplate: () => api.get("/inventory/template", { responseType: "blob" }),
};
