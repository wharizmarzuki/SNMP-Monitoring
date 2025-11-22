# SNMP Monitoring System - Diagrams

This directory contains comprehensive system diagrams for the SNMP Monitoring System, created using Mermaid diagram syntax.

## Available Diagrams

### 1. [Use Case Diagram](use-case-diagram.md)
Illustrates the actors and use cases in the system.

**Shows:**
- Primary actors (Administrator, Background Services, Email Service, SNMP Devices)
- Key use cases grouped by functionality
- Relationships between actors and use cases

**Use this diagram to:**
- Understand system functionality from a user perspective
- Identify who interacts with the system and how
- Document functional requirements

### 2. [Data Flow Diagram](data-flow-diagram.md)
Demonstrates how data flows through the system at multiple levels.

**Includes:**
- Level 0: Context diagram (high-level system view)
- Level 1: Main processes and data stores
- Level 2: Detailed view of the metrics polling process

**Shows:**
- Data movement between processes
- Database interactions
- External system communications

**Use this diagram to:**
- Understand data transformations
- Trace information flow through the system
- Identify data storage points

### 3. [Flow Charts](flowchart.md)
Detailed procedural flowcharts for key processes.

**Contains flowcharts for:**
- Device Discovery Process
- Device Polling Process
- Alert Evaluation Process
- User Authentication Flow
- Email Notification Process

**Shows:**
- Decision points
- Process sequences
- Error handling paths
- Loop iterations

**Use this diagram to:**
- Understand process logic step-by-step
- Debug system behavior
- Optimize workflows
- Document business logic

### 4. [Database Design](database-design.md)
Complete database schema with Entity Relationship Diagram (ERD).

**Includes:**
- ER diagram showing all tables and relationships
- Detailed field descriptions
- SNMP OID mappings
- Sample queries
- Indexing strategy

**Shows:**
- Table structures
- Relationships and cardinality
- Data types and constraints
- Keys and indexes

**Use this diagram to:**
- Understand data model
- Design database queries
- Plan schema migrations
- Optimize database performance

## Viewing Mermaid Diagrams

### GitHub
Mermaid diagrams render automatically when viewing `.md` files on GitHub.

### VS Code
Install the **Mermaid Preview** extension:
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Mermaid Preview"
4. Install and restart

### Online Editors
- [Mermaid Live Editor](https://mermaid.live/)
- Copy the diagram code and paste into the editor

### Documentation Tools
Many documentation platforms support Mermaid:
- GitBook
- Docusaurus
- MkDocs (with plugin)
- Confluence (with plugin)

## Diagram Update Guidelines

When updating these diagrams:

1. **Keep diagrams in sync with code**: Update diagrams when system architecture changes
2. **Use consistent styling**: Follow the color coding used in existing diagrams
3. **Test rendering**: Verify diagrams render correctly before committing
4. **Document changes**: Update this README if adding new diagrams
5. **Version control**: Commit diagram changes alongside related code changes

## Color Coding Convention

Our diagrams use consistent colors for better readability:

- **Blue** (`#e1f5ff`): Start points, user-initiated actions, authentication
- **Green** (`#e1ffe1`): Successful end states, data storage operations
- **Red** (`#ffe1e1`): Error states, failed operations
- **Yellow** (`#fff4e1`): Decision points, conditional logic, background services
- **Pink** (`#ffe1f5`): SNMP operations, device interactions
- **Purple** (`#f5e1ff`): Data processing, calculations

## Quick Reference

| Diagram Type | File | Best For |
|--------------|------|----------|
| Use Case | `use-case-diagram.md` | Understanding features and actors |
| Data Flow | `data-flow-diagram.md` | Tracing data through the system |
| Flow Chart | `flowchart.md` | Understanding process logic |
| Database | `database-design.md` | Understanding data model |

## Related Documentation

- [Project README](../../README.md) - Main project documentation
- [Deployment Guide](../DEPLOYMENT.md) - Production deployment instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)

## Contributing

When contributing new diagrams:

1. Use Mermaid syntax for consistency
2. Place diagrams in this directory
3. Update this README with the new diagram information
4. Ensure diagrams are well-commented and clearly labeled
5. Test rendering across different platforms

## Feedback

If you notice any discrepancies between the diagrams and the actual implementation, please:
1. Open an issue on GitHub
2. Submit a pull request with corrections
3. Contact the development team

---

**Last Updated:** 2025-11-22
**Maintainer:** Development Team
