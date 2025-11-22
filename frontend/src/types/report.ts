// Report data types

export interface NetworkThroughputDatapoint {
  timestamp: string;
  total_inbound_bps: number;
  total_outbound_bps: number;
}

export interface ReportDeviceUtilizationDatapoint {
  timestamp: string;
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  max_cpu_utilization: number;
  max_memory_utilization: number;
  devices_sampled: number;
}

export interface PacketDropRecord {
  device_hostname: string;
  device_ip: string;
  discard_rate_pct: number;
  total_discards_in: number;
  total_discards_out: number;
  total_errors_in: number;
  total_errors_out: number;
}

export interface UptimeSummaryResponse {
  avg_uptime_days: number;
  longest_uptime: {
    hostname: string;
    ip: string;
    uptime_days: number;
  };
  recently_rebooted: {
    hostname: string;
    ip: string;
    uptime_days: number;
  };
}

export interface AvailabilityRecord {
  device_hostname: string;
  device_ip: string;
  availability_pct: number;
  avg_uptime_days: number;
  last_seen: string;
}
