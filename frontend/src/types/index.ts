// Device types
export interface Device {
  ip_address: string;
  hostname: string;
  vendor: string;
  mac_address: string;
  cpu_utilization?: number;
  memory_utilization?: number;
  cpu_threshold?: number;
  memory_threshold?: number;
  last_poll_success?: string;
  is_reachable?: boolean;
  failure_threshold?: number;
  reachability_alert_sent?: boolean;
  status?: string;
}
// Network summary
export interface NetworkSummary {
  total_devices: number;
  devices_up: number;
  devices_in_alert: number;
}

// Alert types
export interface Alert {
  ip_address: string;
  hostname: string;
  metric: string;
  current_value: string; // Changed from number
  threshold: string; // Changed from number
  severity: "Warning" | "High" | "Critical";
  timestamp?: string;
  if_index?: number; // For interface-related alerts
}

// Metric types
export interface DeviceMetric {
  timestamp: string;
  cpu_utilization?: number;
  memory_utilization?: number;
}

export interface InterfaceMetric {
  if_index: number;
  if_name: string;
  oper_status: number;
  octets_in: number;
  octets_out: number;
  discards_in: number;
  errors_in: number;
  discards_out: number;
  errors_out: number;
  packet_drop_threshold?: number;
}

// Top device types
export interface TopDevice {
  hostname: string;
  ip_address: string;
  value: number;
}

// Throughput types
export interface NetworkThroughput {
  timestamp: string;
  inbound_bps: number;
  outbound_bps: number;
}

// Configuration types
export interface Recipient {
  email: string;
}

// History types
export interface HistoryRecord {
  timestamp: string;
  cpu_utilization?: number;
  memory_utilization?: number;
  [key: string]: any;
}
