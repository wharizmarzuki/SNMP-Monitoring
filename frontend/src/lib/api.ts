import axios, { AxiosError } from "axios";
import type { components } from "@/types/api";

// Type aliases from generated OpenAPI types
export type DeviceResponse = components["schemas"]["DeviceResponse"];
export type NetworkSummaryResponse = components["schemas"]["NetworkSummaryResponse"];
export type ActiveAlertResponse = components["schemas"]["ActiveAlertResponse"];
export type DeviceMetricResponse = components["schemas"]["DeviceMetricResponse"];
export type InterfaceSummaryResponse = components["schemas"]["InterfaceSummaryResponse"];
export type TopDeviceResponse = components["schemas"]["TopDeviceResponse"];
export type ThroughputDatapoint = components["schemas"]["ThroughputDatapoint"];
export type RecipientResponse = components["schemas"]["RecipientResponse"];
export type HistoryRecordResponse = components["schemas"]["HistoryRecordResponse"];
export type AlertStateResponse = components["schemas"]["AlertStateResponse"];
export type ThresholdBatchUpdate = components["schemas"]["ThresholdBatchUpdate"];
export type DiscoveryResponse = components["schemas"]["DiscoveryResponse"];

// Configure base URL - update this to match your backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Add response interceptor for standardized error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{error_code: string, message: string, details?: any}>) => {
    if (error.response?.data) {
      const { error_code, message, details } = error.response.data;

      // Log for debugging
      console.error(`API Error [${error_code}]:`, message, details);

      // Return structured error for React Query
      return Promise.reject({
        code: error_code,
        message,
        details,
        status: error.response.status
      });
    }
    return Promise.reject(error);
  }
);

// API endpoints for devices with proper typing
export const deviceApi = {
  getAll: async () => {
    const response = await api.get<DeviceResponse[]>("/device/");
    return response.data;
  },

  getByIp: async (ip: string) => {
    const response = await api.get<DeviceResponse>(`/device/${ip}`);
    return response.data;
  },

  // Create device with SNMP validation
  create: async (deviceData: { ip_address: string; hostname?: string; validate?: boolean }) => {
    const params = deviceData.validate === false ? '?validate=false' : '';
    const response = await api.post(`/device/${params}`, deviceData);
    return response.data;
  },

  // Delete device
  delete: async (ip: string) => {
    const response = await api.delete(`/device/${ip}`);
    return response.data;
  },

  discover: async (network?: string, subnet?: string) => {
    const params = new URLSearchParams();
    if (network) params.append('network', network);
    if (subnet) params.append('subnet', subnet);
    const queryString = params.toString();
    const response = await api.get<DiscoveryResponse>(`/device/discover${queryString ? `?${queryString}` : ''}`);
    return response.data;
  },

  // Batch threshold update (typed with generated schema)
  updateThresholds: async (ip: string, thresholds: ThresholdBatchUpdate) => {
    const response = await api.put<DeviceResponse>(`/device/${ip}/thresholds`, thresholds);
    return response.data;
  },

  // Interface threshold update
  updateInterfaceThreshold: async (ip: string, ifIndex: number, threshold: number) => {
    const response = await api.put<AlertStateResponse>(
      `/device/${ip}/interface/${ifIndex}/threshold`,
      { threshold_value: threshold }
    );
    return response.data;
  },

  // Maintenance mode
  updateMaintenanceMode: async (
    ip: string,
    data: { enabled: boolean; duration_minutes?: number; reason?: string }
  ) => {
    const response = await api.put(`/device/${ip}/maintenance`, data);
    return response.data;
  },

  // Acknowledge alert endpoints
  acknowledgeDeviceAlert: async (ip: string, alertType: "cpu" | "memory" | "reachability") => {
    const response = await api.put<AlertStateResponse>(`/device/${ip}/alert/${alertType}/acknowledge`);
    return response.data;
  },

  acknowledgeInterfaceAlert: async (ip: string, ifIndex: number, alertType: "status" | "drops") => {
    const response = await api.put<AlertStateResponse>(
      `/device/${ip}/interface/${ifIndex}/alert/${alertType}/acknowledge`
    );
    return response.data;
  },

  // Resolve alert endpoints
  resolveDeviceAlert: async (ip: string, alertType: "cpu" | "memory" | "reachability") => {
    const response = await api.put<AlertStateResponse>(`/device/${ip}/alert/${alertType}/resolve`);
    return response.data;
  },

  resolveInterfaceAlert: async (ip: string, ifIndex: number, alertType: "status" | "drops") => {
    const response = await api.put<AlertStateResponse>(
      `/device/${ip}/interface/${ifIndex}/alert/${alertType}/resolve`
    );
    return response.data;
  },
};

// Types for application settings
export interface ApplicationSettings {
  id: number;
  snmp_community: string;
  snmp_timeout: number;
  snmp_retries: number;
  polling_interval: number;
  discovery_concurrency: number;
  polling_concurrency: number;
  smtp_server: string;
  smtp_port: number;
  sender_email: string | null;
  sender_password: string | null;
  discovery_network: string | null;
  updated_at: string;
}

export interface ApplicationSettingsUpdate {
  snmp_community?: string;
  snmp_timeout?: number;
  snmp_retries?: number;
  polling_interval?: number;
  discovery_concurrency?: number;
  polling_concurrency?: number;
  smtp_server?: string;
  smtp_port?: number;
  sender_email?: string;
  sender_password?: string;
  discovery_network?: string;
}

// API endpoints for configuration with proper typing
export const configApi = {
  getRecipients: async () => {
    const response = await api.get<RecipientResponse[]>("/recipients/");
    return response.data;
  },

  addRecipient: async (email: string) => {
    const response = await api.post<RecipientResponse>("/recipients/", { email });
    return response.data;
  },

  deleteRecipient: async (id: number) => {
    await api.delete(`/recipients/${id}`);
  },

  getSettings: async () => {
    const response = await api.get<ApplicationSettings>("/settings/");
    return response.data;
  },

  updateSettings: async (settings: ApplicationSettingsUpdate) => {
    const response = await api.patch<ApplicationSettings>("/settings/", settings);
    return response.data;
  },
};

// API endpoints for queries with proper typing
export const queryApi = {
  getNetworkSummary: async () => {
    const response = await api.get<NetworkSummaryResponse>("/query/network-summary");
    return response.data;
  },

  getTopDevices: async (metric: "cpu" | "memory") => {
    const response = await api.get<TopDeviceResponse[]>(`/query/top-devices?metric=${metric}`);
    return response.data;
  },

  getDeviceMetrics: async (ip: string) => {
    const response = await api.get<DeviceMetricResponse[]>(`/query/device/${ip}/metrics`);
    return response.data;
  },

  // Optimized interface summary endpoint (60-80% smaller payload)
  getInterfaceSummary: async (ip: string) => {
    const response = await api.get<InterfaceSummaryResponse[]>(`/query/device/${ip}/interfaces/summary`);
    return response.data;
  },

  getHistory: async (ip: string, start: string, end: string) => {
    const response = await api.post<HistoryRecordResponse[]>(
      `/query/history/device`,
      {
        ip_address: ip,
        start_datetime: start,
        end_datetime: end
      }
    );
    return response.data;
  },

  getActiveAlerts: async () => {
    const response = await api.get<ActiveAlertResponse[]>("/query/alerts/active");
    return response.data;
  },

  getNetworkThroughput: async () => {
    const response = await api.get<ThroughputDatapoint[]>("/query/network-throughput");
    return response.data;
  },
};

// API endpoints for polling
export const pollingApi = {
  triggerPoll: async () => {
    const response = await api.get("/polling/");
    return response.data;
  },
};

// API endpoints for health monitoring
export const healthApi = {
  getHealth: async () => {
    const response = await api.get("/health");
    return response.data;
  },

  getDatabase: async () => {
    const response = await api.get("/health/database");
    return response.data;
  },

  getRedis: async () => {
    const response = await api.get("/health/redis");
    return response.data;
  },

  getServices: async () => {
    const response = await api.get("/health/services");
    return response.data;
  },

  ping: async () => {
    const response = await api.get("/ping");
    return response.data;
  },
};
