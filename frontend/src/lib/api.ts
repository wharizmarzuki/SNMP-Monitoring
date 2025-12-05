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
export type AlertStateResponse = components["schemas"]["AlertStateResponse"];
export type ThresholdBatchUpdate = components["schemas"]["ThresholdBatchUpdate"];
export type DiscoveryResponse = components["schemas"]["DiscoveryResponse"];
export type AlertHistoryResponse = components["schemas"]["AlertHistoryResponse"];
export type AlertHistoryDetailResponse = components["schemas"]["AlertHistoryDetailResponse"];
export type AlertHistoryStatsResponse = components["schemas"]["AlertHistoryStatsResponse"];

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
    // Handle structured API errors
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

    // Handle network errors, timeouts, and other non-API errors
    let errorMessage = "An unexpected error occurred";

    if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
      errorMessage = "Unable to connect to server. Please check your connection.";
    } else if (error.code === 'ETIMEDOUT') {
      errorMessage = "Request timeout. Please try again.";
    } else if (error.response?.status === 401) {
      errorMessage = "Invalid username or password";
    } else if (error.response?.status === 403) {
      errorMessage = "Access denied";
    } else if (error.response?.status === 404) {
      errorMessage = "Resource not found";
    } else if (error.response?.status === 500) {
      errorMessage = "Server error. Please try again later.";
    } else if (error.message) {
      errorMessage = error.message;
    }

    console.error("Network/API Error:", errorMessage, error);

    // Return structured error with message property
    return Promise.reject({
      code: error.code || 'UNKNOWN_ERROR',
      message: errorMessage,
      status: error.response?.status,
      originalError: error
    });
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

  // Acknowledge alert endpoints (using consolidated endpoints)
  acknowledgeDeviceAlert: async (ip: string, alertType: "cpu" | "memory" | "reachability") => {
    const response = await api.patch<AlertStateResponse>(
      `/device/${ip}/alerts/${alertType}`,
      { action: "acknowledge" }
    );
    return response.data;
  },

  acknowledgeInterfaceAlert: async (ip: string, ifIndex: number, alertType: "status" | "drops") => {
    const response = await api.patch<AlertStateResponse>(
      `/device/${ip}/interfaces/${ifIndex}/alerts/${alertType}`,
      { action: "acknowledge" }
    );
    return response.data;
  },

  // Resolve alert endpoints (using consolidated endpoints)
  resolveDeviceAlert: async (ip: string, alertType: "cpu" | "memory" | "reachability") => {
    const response = await api.patch<AlertStateResponse>(
      `/device/${ip}/alerts/${alertType}`,
      { action: "resolve" }
    );
    return response.data;
  },

  resolveInterfaceAlert: async (ip: string, ifIndex: number, alertType: "status" | "drops") => {
    const response = await api.patch<AlertStateResponse>(
      `/device/${ip}/interfaces/${ifIndex}/alerts/${alertType}`,
      { action: "resolve" }
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

  getDeviceMetrics: async (ip: string, minutes?: number, intervalMinutes?: number) => {
    const params = new URLSearchParams();
    if (minutes) params.append('minutes', minutes.toString());
    if (intervalMinutes) params.append('interval_minutes', intervalMinutes.toString());
    const queryString = params.toString();
    const response = await api.get<DeviceMetricResponse[]>(
      `/query/device/${ip}/metrics${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },

  // Optimized interface summary endpoint (60-80% smaller payload)
  getInterfaceSummary: async (ip: string) => {
    const response = await api.get<InterfaceSummaryResponse[]>(`/query/device/${ip}/interfaces/summary`);
    return response.data;
  },

  getHistory: async (ip: string, start: string, end: string) => {
    // Append time component to dates (start of day for start_time, end of day for end_time)
    const startDateTime = start.includes('T') ? start : `${start}T00:00:00`;
    const endDateTime = end.includes('T') ? end : `${end}T23:59:59`;

    const response = await api.post<DeviceMetricResponse[]>(
      `/query/history/device`,
      {
        ip_address: ip,
        start_time: startDateTime,
        end_time: endDateTime
      }
    );
    return response.data;
  },

  getActiveAlerts: async () => {
    const response = await api.get<ActiveAlertResponse[]>("/query/alerts/active");
    return response.data;
  },

  // Alert History endpoints
  getAlertHistory: async (params?: {
    alert_type?: string;
    severity?: string;
    device_id?: number;
    interface_id?: number;
    start_time?: string;
    end_time?: string;
    include_cleared?: boolean;
    page?: number;
    per_page?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.alert_type) queryParams.append('alert_type', params.alert_type);
    if (params?.severity) queryParams.append('severity', params.severity);
    if (params?.device_id) queryParams.append('device_id', params.device_id.toString());
    if (params?.interface_id) queryParams.append('interface_id', params.interface_id.toString());
    if (params?.start_time) queryParams.append('start_time', params.start_time);
    if (params?.end_time) queryParams.append('end_time', params.end_time);
    if (params?.include_cleared !== undefined) queryParams.append('include_cleared', params.include_cleared.toString());
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.per_page) queryParams.append('per_page', params.per_page.toString());

    const queryString = queryParams.toString();
    const response = await api.get<AlertHistoryResponse[]>(`/alerts/history${queryString ? `?${queryString}` : ''}`);
    return response.data;
  },

  getAlertHistoryDetail: async (alertId: number) => {
    const response = await api.get<AlertHistoryDetailResponse>(`/alerts/history/${alertId}`);
    return response.data;
  },

  getAlertHistoryStats: async (params?: {
    start_time?: string;
    end_time?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.start_time) queryParams.append('start_time', params.start_time);
    if (params?.end_time) queryParams.append('end_time', params.end_time);

    const queryString = queryParams.toString();
    const response = await api.get<AlertHistoryStatsResponse>(`/alerts/history/stats${queryString ? `?${queryString}` : ''}`);
    return response.data;
  },

  getNetworkThroughput: async () => {
    const response = await api.get<ThroughputDatapoint[]>("/query/network-throughput");
    return response.data;
  },

  getDeviceUtilization: async (minutes?: number, intervalMinutes?: number) => {
    const params = new URLSearchParams();
    if (minutes) params.append('minutes', minutes.toString());
    if (intervalMinutes) params.append('interval_minutes', intervalMinutes.toString());
    const queryString = params.toString();
    const response = await api.get<import("@/types").DeviceUtilization[]>(
      `/query/device-utilization${queryString ? `?${queryString}` : ''}`
    );
    return response.data;
  },
};

// API endpoints for polling
export const pollingApi = {
  triggerPoll: async () => {
    const response = await api.get("/polling/");
    return response.data;
  },
  getStatus: async () => {
    const response = await api.get<{ is_polling: boolean; polling_type: string | null }>("/polling/status");
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

// API endpoints for reports
export const reportApi = {
  getNetworkThroughput: async (startDate: string, endDate: string) => {
    const response = await api.get<import("@/types/report").NetworkThroughputDatapoint[]>(
      "/query/report/network-throughput",
      { params: { start_date: startDate, end_date: endDate } }
    );
    return response.data;
  },

  getDeviceUtilization: async (startDate: string, endDate: string) => {
    const response = await api.get<import("@/types/report").ReportDeviceUtilizationDatapoint[]>(
      "/query/report/device-utilization",
      { params: { start_date: startDate, end_date: endDate } }
    );
    return response.data;
  },

  getPacketDrops: async (startDate: string, endDate: string) => {
    const response = await api.get<import("@/types/report").PacketDropRecord[]>(
      "/query/report/packet-drops",
      { params: { start_date: startDate, end_date: endDate } }
    );
    return response.data;
  },

  getUptimeSummary: async (startDate: string, endDate: string) => {
    const response = await api.get<import("@/types/report").UptimeSummaryResponse>(
      "/query/report/uptime-summary",
      { params: { start_date: startDate, end_date: endDate } }
    );
    return response.data;
  },

  getAvailability: async (startDate: string, endDate: string) => {
    const response = await api.get<import("@/types/report").AvailabilityRecord[]>(
      "/query/report/availability",
      { params: { start_date: startDate, end_date: endDate } }
    );
    return response.data;
  },
};
