import axios from "axios";

// Configure base URL - update this to match your backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// API endpoints for devices
export const deviceApi = {
  getAll: () => api.get("/device/"),
  getByIp: (ip: string) => api.get(`/device/${ip}`),
  discover: () => api.get("/device/discover"),
  updateCpuThreshold: (ip: string, threshold: number) =>
    api.put(`/device/${ip}/threshold/cpu`, { threshold_value: threshold }),
  updateMemoryThreshold: (ip: string, threshold: number) =>
    api.put(`/device/${ip}/threshold/memory`, { threshold_value: threshold }),
  updateInterfaceThreshold: (ip: string, ifIndex: number, threshold: number) =>
    api.put(`/device/${ip}/interface/${ifIndex}/threshold`, {
      threshold_value: threshold,
    }),
  updateReachabilityThreshold: (ip: string, threshold: number) =>
    api.put(`/device/${ip}/threshold/reachability`, { threshold_value: threshold }),

  // Acknowledge alert endpoints
  acknowledgeDeviceAlert: (ip: string, alertType: "cpu" | "memory" | "reachability") =>
    api.put(`/device/${ip}/alert/${alertType}/acknowledge`),
  acknowledgeInterfaceAlert: (ip: string, ifIndex: number, alertType: "status" | "drops") =>
    api.put(`/device/${ip}/interface/${ifIndex}/alert/${alertType}/acknowledge`),

  // Resolve alert endpoints
  resolveDeviceAlert: (ip: string, alertType: "cpu" | "memory" | "reachability") =>
    api.put(`/device/${ip}/alert/${alertType}/resolve`),
  resolveInterfaceAlert: (ip: string, ifIndex: number, alertType: "status" | "drops") =>
    api.put(`/device/${ip}/interface/${ifIndex}/alert/${alertType}/resolve`),
};

// API endpoints for configuration
export const configApi = {
  getRecipients: () => api.get("/recipients/"),
  addRecipient: (email: string) => api.post("/recipients/", { email }),
  deleteRecipient: (email: string) => api.delete(`/recipients/${email}`),
};

// API endpoints for queries
export const queryApi = {
  getNetworkSummary: () => api.get("/query/network-summary"),
  getTopDevices: (metric: "cpu" | "memory") =>
    api.get(`/query/top-devices?metric=${metric}`),
  getDeviceMetrics: (ip: string) => api.get(`/query/device/${ip}/metrics`),
  getDeviceInterfaces: (ip: string) =>
    api.get(`/query/device/${ip}/interfaces`),
  getHistory: (ip: string, start: string, end: string) =>
    api.get(`/query/history/device?ip=${ip}&start=${start}&end=${end}`),
  getActiveAlerts: () => api.get("/query/alerts/active"),
  getNetworkThroughput: () => api.get("/query/network-throughput"),
};
