// Re-export auto-generated types from OpenAPI schema
// These types are now auto-generated from backend OpenAPI spec
export type {
  DeviceResponse,
  NetworkSummaryResponse,
  ActiveAlertResponse,
  DeviceMetricResponse,
  InterfaceSummaryResponse,
  TopDeviceResponse,
  ThroughputDatapoint,
  RecipientResponse,
  HistoryRecordResponse,
  AlertStateResponse,
  ThresholdBatchUpdate,
  DiscoveryResponse,
} from "@/lib/api";

// Legacy type aliases for backwards compatibility
// Components can continue using old names while we migrate
export type Device = import("@/lib/api").DeviceResponse;
export type NetworkSummary = import("@/lib/api").NetworkSummaryResponse;
export type Alert = import("@/lib/api").ActiveAlertResponse;
export type DeviceMetric = import("@/lib/api").DeviceMetricResponse;
export type InterfaceMetric = import("@/lib/api").InterfaceSummaryResponse;
export type TopDevice = import("@/lib/api").TopDeviceResponse;
export type NetworkThroughput = import("@/lib/api").ThroughputDatapoint;
export type Recipient = import("@/lib/api").RecipientResponse;
export type HistoryRecord = import("@/lib/api").HistoryRecordResponse;

// Device utilization type (manually defined until OpenAPI regeneration)
export interface DeviceUtilization {
  device_id: number;
  hostname: string | null;
  ip_address: string | null;
  timestamp: string;
  inbound_bps: number;
  outbound_bps: number;
  total_capacity_bps: number | null;
  utilization_in_pct: number | null;
  utilization_out_pct: number | null;
  max_utilization_pct: number | null;
}
