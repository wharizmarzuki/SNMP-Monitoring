# Page snapshot

```yaml
- generic [ref=e1]:
  - main [ref=e3]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - heading "SNMP Monitoring System" [level=3] [ref=e7]
        - paragraph [ref=e8]: Enter your credentials to access the monitoring dashboard
      - generic [ref=e9]:
        - generic [ref=e10]:
          - generic [ref=e11]:
            - text: Username
            - textbox "Username" [active] [ref=e12]:
              - /placeholder: Enter your username
          - generic [ref=e13]:
            - text: Password
            - textbox "Password" [ref=e14]:
              - /placeholder: Enter your password
              - text: wrongpassword
          - button "Sign in" [ref=e15] [cursor=pointer]
        - generic [ref=e16]:
          - paragraph [ref=e17]: First time setup?
          - paragraph [ref=e18]:
            - text: Run
            - code [ref=e19]: python scripts/setup_admin.py
            - text: to create an admin user
  - alert [ref=e20]
```