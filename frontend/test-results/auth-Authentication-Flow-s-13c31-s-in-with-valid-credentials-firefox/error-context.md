# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e3]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - heading "SNMP Monitoring System" [level=3] [ref=e7]
        - paragraph [ref=e8]: Enter your credentials to access the monitoring dashboard
      - generic [ref=e9]:
        - generic [ref=e10]:
          - generic [ref=e11]:
            - text: Username
            - textbox "Username" [disabled] [ref=e12]:
              - /placeholder: Enter your username
              - text: admin
          - generic [ref=e13]:
            - text: Password
            - textbox "Password" [disabled] [ref=e14]:
              - /placeholder: Enter your password
              - text: password
          - button "Signing in..." [disabled]
        - generic [ref=e15]:
          - paragraph [ref=e16]: First time setup?
          - paragraph [ref=e17]:
            - text: Run
            - code [ref=e18]: python scripts/setup_admin.py
            - text: to create an admin user
  - alert [ref=e19]
```