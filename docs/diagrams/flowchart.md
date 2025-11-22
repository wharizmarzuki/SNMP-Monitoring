# System Flow Charts

This document contains detailed flowcharts for the main processes in the SNMP Monitoring System.

## 1. Device Discovery Process

```mermaid
flowchart TD
    Start([Admin Triggers Discovery]) --> GetConfig[Load Network Config<br/>from Settings]
    GetConfig --> ParseNetwork{Valid CIDR<br/>Network?}

    ParseNetwork -->|No| Error1[Log Error: Invalid Network]
    Error1 --> End1([Return Empty Result])

    ParseNetwork -->|Yes| GenerateIPs[Generate List of<br/>Host IP Addresses]
    GenerateIPs --> CreateTasks[Create Concurrent<br/>Discovery Tasks]

    CreateTasks --> Loop{For Each IP<br/>Address}

    Loop --> CreateSession[Create New DB Session<br/>for Task]
    CreateSession --> SendSNMP[Send SNMP GET Request<br/>to Device]

    SendSNMP --> CheckResponse{SNMP<br/>Response<br/>Received?}

    CheckResponse -->|No| CloseSession1[Close DB Session]
    CloseSession1 --> Loop

    CheckResponse -->|Yes| ExtractData[Extract Device Info:<br/>- Hostname<br/>- MAC Address<br/>- Vendor<br/>- IP Address]

    ExtractData --> CheckExists{Device<br/>Exists in DB?}

    CheckExists -->|Yes| UpdateDevice[Update Existing Device<br/>Information]
    CheckExists -->|No| CreateDevice[Create New Device<br/>Record]

    UpdateDevice --> SaveDB[Commit to Database]
    CreateDevice --> SaveDB

    SaveDB --> CloseSession2[Close DB Session]
    CloseSession2 --> Loop

    Loop -->|All IPs Processed| GatherResults[Gather All Results]
    GatherResults --> LogSummary[Log Discovery Summary:<br/>Total Scanned, Devices Found]
    LogSummary --> End2([Return Discovery Results])

    style Start fill:#e1f5ff
    style End1 fill:#ffe1e1
    style End2 fill:#e1ffe1
    style CheckResponse fill:#fff4e1
    style ParseNetwork fill:#fff4e1
    style CheckExists fill:#fff4e1
```

## 2. Device Polling Process

```mermaid
flowchart TD
    Start([Scheduled Poll Triggered]) --> LoadSettings[Load Runtime Settings:<br/>- Polling Interval<br/>- Concurrency Limit]

    LoadSettings --> FetchDevices[Fetch All Devices<br/>from Database]

    FetchDevices --> CheckDevices{Any Devices<br/>to Poll?}

    CheckDevices -->|No| LogEmpty[Log: No Devices to Poll]
    LogEmpty --> End1([End Poll Cycle])

    CheckDevices -->|Yes| CreateSemaphore[Create Semaphore<br/>with Concurrency Limit]

    CreateSemaphore --> LoopDevices{For Each<br/>Device}

    LoopDevices --> CreateSession[Create New DB Session]
    CreateSession --> MarkAttempt[Mark Poll Attempt Time]

    MarkAttempt --> SendDevicePoll[Send SNMP GET:<br/>CPU, Memory, Uptime OIDs]

    SendDevicePoll --> PollSuccess{SNMP<br/>Success?}

    PollSuccess -->|No| IncrementFail[Increment<br/>Consecutive Failures]

    IncrementFail --> CheckThreshold{Failures >=<br/>Threshold?}

    CheckThreshold -->|Yes| MarkUnreachable[Mark Device as<br/>Unreachable]
    MarkUnreachable --> EvalReachAlert1[Evaluate Reachability<br/>Alert]

    CheckThreshold -->|No| EvalReachAlert1

    EvalReachAlert1 --> SaveFail[Save Device State]
    SaveFail --> CloseSession1[Close DB Session]
    CloseSession1 --> LoopDevices

    PollSuccess -->|Yes| ResetFailures[Reset Consecutive<br/>Failures to 0]

    ResetFailures --> CheckWasDown{Was Device<br/>Previously<br/>Unreachable?}

    CheckWasDown -->|Yes| MarkReachable[Mark Device as<br/>Reachable]
    CheckWasDown -->|No| CalculateMetrics[Calculate Metrics:<br/>- CPU Utilization %<br/>- Memory Utilization %]
    MarkReachable --> CalculateMetrics

    CalculateMetrics --> EvalCPU[Evaluate CPU Alert]
    EvalCPU --> EvalMemory[Evaluate Memory Alert]
    EvalMemory --> EvalReachAlert2[Evaluate Reachability Alert]

    EvalReachAlert2 --> SaveMetric[Save Device Metric<br/>to Database]

    SaveMetric --> CheckMaintenance{Device in<br/>Maintenance<br/>Mode?}

    CheckMaintenance -->|Yes| SkipInterfaces[Skip Interface Polling]
    SkipInterfaces --> Commit1[Commit DB Session]

    CheckMaintenance -->|No| PollInterfaces[Poll Interfaces]

    PollInterfaces --> SendBulkWalk[Send SNMP BULK WALK<br/>for Interface OIDs]

    SendBulkWalk --> InterfaceSuccess{SNMP<br/>Success?}

    InterfaceSuccess -->|No| Commit1

    InterfaceSuccess -->|Yes| GroupByIndex[Group Interface Data<br/>by ifIndex]

    GroupByIndex --> LoopInterfaces{For Each<br/>Interface}

    LoopInterfaces --> CheckIfExists{Interface<br/>Exists?}

    CheckIfExists -->|No| CreateInterface[Create Interface Record]
    CheckIfExists -->|Yes| UpdateInterface[Update Interface Info<br/>- Speed<br/>- Name]

    CreateInterface --> SaveIfMetric[Save Interface Metric:<br/>- Status<br/>- Octets In/Out<br/>- Errors<br/>- Discards]
    UpdateInterface --> SaveIfMetric

    SaveIfMetric --> LoopInterfaces

    LoopInterfaces -->|All Processed| EvalIfAlerts[Evaluate Interface Alerts:<br/>- Operational Status<br/>- Packet Drops]

    EvalIfAlerts --> Commit1
    Commit1 --> CloseSession2[Close DB Session]
    CloseSession2 --> LoopDevices

    LoopDevices -->|All Processed| LogSummary[Log Poll Summary:<br/>Successful, Failed]
    LogSummary --> End2([End Poll Cycle])

    style Start fill:#e1f5ff
    style End1 fill:#ffe1e1
    style End2 fill:#e1ffe1
    style PollSuccess fill:#fff4e1
    style CheckDevices fill:#fff4e1
    style CheckThreshold fill:#fff4e1
    style InterfaceSuccess fill:#fff4e1
    style CheckMaintenance fill:#fff4e1
```

## 3. Alert Evaluation Process

```mermaid
flowchart TD
    Start([Metric Received]) --> CheckMaint{Device in<br/>Maintenance<br/>Mode?}

    CheckMaint -->|Yes| CheckExpired{Maintenance<br/>Window<br/>Expired?}

    CheckExpired -->|No| SuppressAlert[Suppress All Alerts]
    SuppressAlert --> End1([Return: No Alert])

    CheckExpired -->|Yes| DisableMaint[Disable Maintenance Mode]
    DisableMaint --> EvalThreshold

    CheckMaint -->|No| EvalThreshold{Current Value ><br/>Threshold?}

    EvalThreshold -->|Yes - Exceeded| CheckState1{Current<br/>Alert State?}

    CheckState1 -->|Clear| SendAlert[Send Alert Email<br/>to Recipients]
    SendAlert --> SetTriggered[Set State to 'triggered']
    SetTriggered --> SaveState1[Save Device/Interface<br/>State to DB]
    SaveState1 --> End2([Return: Alert Sent])

    CheckState1 -->|Triggered| NoAction1[No Action<br/>Already Alerted]
    NoAction1 --> End3([Return: No Change])

    CheckState1 -->|Acknowledged| NoAction2[No Action<br/>User Acknowledged]
    NoAction2 --> End3

    EvalThreshold -->|No - Normal| CheckState2{Current<br/>Alert State?}

    CheckState2 -->|Clear| NoAction3[No Action<br/>Still Normal]
    NoAction3 --> End3

    CheckState2 -->|Triggered or<br/>Acknowledged| SendRecovery[Send Recovery Email<br/>to Recipients]
    SendRecovery --> SetClear[Set State to 'clear'<br/>Clear Acknowledgment]
    SetClear --> SaveState2[Save Device/Interface<br/>State to DB]
    SaveState2 --> End4([Return: Recovery Sent])

    style Start fill:#e1f5ff
    style End1 fill:#ffe1e1
    style End2 fill:#e1ffe1
    style End3 fill:#fff4e1
    style End4 fill:#e1ffe1
    style CheckMaint fill:#fff4e1
    style EvalThreshold fill:#fff4e1
    style CheckState1 fill:#fff4e1
    style CheckState2 fill:#fff4e1
```

## 4. User Authentication Flow

```mermaid
flowchart TD
    Start([User Submits Login]) --> ReceiveCreds[Receive Username<br/>and Password]

    ReceiveCreds --> QueryUser[Query User from<br/>Database by Username]

    QueryUser --> UserExists{User<br/>Found?}

    UserExists -->|No| Return401[Return 401:<br/>Invalid Credentials]
    Return401 --> End1([Login Failed])

    UserExists -->|Yes| CheckActive{User<br/>is_active?}

    CheckActive -->|No| Return403[Return 403:<br/>Account Disabled]
    Return403 --> End1

    CheckActive -->|Yes| VerifyPassword[Verify Password Hash<br/>using bcrypt]

    VerifyPassword --> PasswordMatch{Password<br/>Correct?}

    PasswordMatch -->|No| Return401

    PasswordMatch -->|Yes| GenerateToken[Generate JWT Token:<br/>- User ID<br/>- Username<br/>- Expiry Time]

    GenerateToken --> ReturnToken[Return Token to Client]
    ReturnToken --> End2([Login Successful])

    style Start fill:#e1f5ff
    style End1 fill:#ffe1e1
    style End2 fill:#e1ffe1
    style UserExists fill:#fff4e1
    style CheckActive fill:#fff4e1
    style PasswordMatch fill:#fff4e1
```

## 5. Email Notification Process

```mermaid
flowchart TD
    Start([Alert Triggered]) --> FetchRecipients[Fetch Alert Recipients<br/>from Database]

    FetchRecipients --> CheckRecipients{Any Recipients<br/>Configured?}

    CheckRecipients -->|No| LogWarning[Log Warning:<br/>No Recipients]
    LogWarning --> End1([Email Not Sent])

    CheckRecipients -->|Yes| BuildEmail[Build Email:<br/>- Subject<br/>- Body with Details]

    BuildEmail --> GetSMTP[Get SMTP Settings:<br/>- Server<br/>- Port<br/>- Credentials]

    GetSMTP --> CreateBgTask[Create Background Task<br/>for Async Sending]

    CreateBgTask --> ConnectSMTP[Connect to SMTP Server<br/>with TLS]

    ConnectSMTP --> SMTPConnect{Connection<br/>Successful?}

    SMTPConnect -->|No| LogError[Log Error:<br/>SMTP Connection Failed]
    LogError --> End2([Email Failed])

    SMTPConnect -->|Yes| SendEmail[Send Email to<br/>All Recipients]

    SendEmail --> EmailSent{Email<br/>Sent?}

    EmailSent -->|No| LogSendError[Log Error:<br/>Send Failed]
    LogSendError --> End2

    EmailSent -->|Yes| LogSuccess[Log Success:<br/>Email Sent]
    LogSuccess --> CloseSMTP[Close SMTP Connection]
    CloseSMTP --> End3([Email Delivered])

    style Start fill:#e1f5ff
    style End1 fill:#ffe1e1
    style End2 fill:#ffe1e1
    style End3 fill:#e1ffe1
    style CheckRecipients fill:#fff4e1
    style SMTPConnect fill:#fff4e1
    style EmailSent fill:#fff4e1
```

## Process Timing

| Process | Frequency | Concurrency Limit |
|---------|-----------|-------------------|
| Device Discovery | On-Demand | Configurable (default: 20) |
| Device Polling | Every 60 seconds (configurable) | Configurable (default: 20) |
| Alert Evaluation | Per Poll | N/A (inline) |
| Email Notifications | On Alert Trigger | Background Tasks |

## Error Handling

All processes implement comprehensive error handling:

1. **Database Session Management**: Each concurrent task gets its own session
2. **Rollback on Failure**: Failed transactions are rolled back
3. **Logging**: All errors logged with context
4. **Graceful Degradation**: System continues operating even if individual devices fail
5. **Retry Logic**: SNMP queries have configurable timeout and retries
