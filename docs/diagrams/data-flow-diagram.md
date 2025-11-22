# Data Flow Diagram (DFD)

This diagram illustrates how data flows through the SNMP Monitoring System.

## Level 0 - Context Diagram

```mermaid
graph LR
    Admin([Administrator])
    Devices([SNMP Devices])
    Email([Email Recipients])

    System[SNMP Monitoring System]

    Admin -->|Login Credentials| System
    Admin -->|Configuration| System
    System -->|Dashboard & Reports| Admin

    Devices -->|SNMP Responses| System
    System -->|SNMP Queries| Devices

    System -->|Alert Emails| Email
```

## Level 1 - Main Processes

```mermaid
graph TB
    subgraph "External Entities"
        Admin([Administrator])
        Devices([Network Devices])
        SMTP([SMTP Server])
    end

    subgraph "SNMP Monitoring System"
        P1[1.0 Authentication]
        P2[2.0 Device Discovery]
        P3[3.0 Metrics Polling]
        P4[4.0 Alert Evaluation]
        P5[5.0 Data Storage]
        P6[6.0 Notification Service]
        P7[7.0 Web Interface]

        D1[(User Database)]
        D2[(Device Database)]
        D3[(Metrics Database)]
        D4[(Settings Database)]
        Cache[(Redis Cache)]
    end

    Admin -->|Login Request| P1
    P1 -->|JWT Token| Admin
    P1 -.->|User Credentials| D1

    Admin -->|Discovery Request| P2
    P2 -->|SNMP Query| Devices
    Devices -->|Device Info| P2
    P2 -->|Device Records| P5
    P5 -->|Store Devices| D2

    P3 -->|SNMP Poll Request| Devices
    Devices -->|Metrics Data| P3
    P3 -->|Raw Metrics| P5
    P5 -->|Store Metrics| D3

    P3 -->|Metric Values| P4
    D2 -.->|Threshold Config| P4
    D4 -.->|Alert Recipients| P4
    P4 -->|Alert State| P5
    P4 -->|Trigger Email| P6

    P6 -->|Email Notification| SMTP
    SMTP -->|Delivered| Admin

    Admin -->|View Request| P7
    P7 -.->|Query Data| D2
    P7 -.->|Query Metrics| D3
    P7 -.->|Cache Lookup| Cache
    Cache -.->|Cached Data| P7
    P7 -->|Dashboard/Reports| Admin

    Admin -->|Settings Update| P7
    P7 -->|Save Config| D4

    style P1 fill:#e1f5ff
    style P2 fill:#ffe1f5
    style P3 fill:#f5e1ff
    style P4 fill:#ffe1e1
    style P5 fill:#e1ffe1
    style P6 fill:#fff4e1
    style P7 fill:#e1f5ff
```

## Level 2 - Metrics Polling Process (Detailed)

```mermaid
graph TB
    subgraph "3.0 Metrics Polling Process"
        P3_1[3.1 Schedule Polling]
        P3_2[3.2 Poll Device Metrics]
        P3_3[3.3 Poll Interface Metrics]
        P3_4[3.4 Calculate Metrics]
        P3_5[3.5 Update Device Status]
    end

    Device([SNMP Device])
    D2[(Device DB)]
    D3[(Metrics DB)]
    AlertProc[4.0 Alert Evaluation]

    D2 -->|Device List| P3_1
    P3_1 -->|Poll Request| P3_2

    P3_2 -->|SNMP GET| Device
    Device -->|CPU/Memory/Uptime| P3_2
    P3_2 -->|Raw Data| P3_4

    P3_3 -->|SNMP BULK WALK| Device
    Device -->|Interface Stats| P3_3
    P3_3 -->|Interface Data| P3_4

    P3_4 -->|Calculate CPU %| P3_4
    P3_4 -->|Calculate Memory %| P3_4
    P3_4 -->|Calculate Bandwidth| P3_4
    P3_4 -->|Calculated Metrics| P3_5

    P3_5 -->|Update Reachability| D2
    P3_5 -->|Save Metrics| D3
    P3_5 -->|Send Metrics| AlertProc

    P3_2 -.->|Poll Failed| P3_5
    P3_5 -.->|Increment Failures| D2

    style P3_1 fill:#e1f5ff
    style P3_2 fill:#ffe1f5
    style P3_3 fill:#f5e1ff
    style P3_4 fill:#ffe1e1
    style P3_5 fill:#e1ffe1
```

## Data Stores

### D1 - User Database
- **Stores**: User accounts, credentials, roles
- **Used by**: Authentication process
- **Format**: SQLite table (users)

### D2 - Device Database
- **Stores**: Device information, IP addresses, hostnames, thresholds, alert states
- **Used by**: All processes
- **Format**: SQLite tables (devices, interfaces)

### D3 - Metrics Database
- **Stores**: Historical metrics data (CPU, memory, interface stats)
- **Used by**: Polling, reporting, alerting
- **Format**: SQLite tables (device_metrics, interface_metrics)

### D4 - Settings Database
- **Stores**: Application settings, SNMP config, SMTP config, alert recipients
- **Used by**: All processes for configuration
- **Format**: SQLite tables (application_settings, alert_recipients)

### Redis Cache
- **Stores**: Temporary cached data for performance
- **Used by**: Web interface
- **Format**: Key-value pairs with TTL

## Data Flow Descriptions

### 1. Authentication Flow
1. Admin submits login credentials
2. System validates against user database
3. JWT token issued for authenticated session

### 2. Discovery Flow
1. Admin triggers network discovery
2. System scans network range via SNMP
3. Discovered devices stored in database
4. Device information updated/created

### 3. Polling Flow
1. Background scheduler triggers polling
2. System queries devices via SNMP
3. Raw metrics collected and calculated
4. Metrics stored in database
5. Alert evaluation triggered

### 4. Alert Flow
1. Metrics compared against thresholds
2. Alert state transitions evaluated
3. Email notifications triggered
4. Alert recipients fetched from database
5. SMTP service sends notifications

### 5. Dashboard Flow
1. Admin requests dashboard view
2. System queries device and metrics databases
3. Cache checked for recent data
4. Data aggregated and formatted
5. Dashboard rendered to admin
