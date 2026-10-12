import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

export const endpoints = {
  login: (employee_id) => api.post("/auth/login", { employee_id }),
  users: () => api.get("/users"),
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
};
