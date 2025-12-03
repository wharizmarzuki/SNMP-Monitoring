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
          - alert [ref=e11]:
            - generic [ref=e12]: Login failed. Please try again.
          - generic [ref=e13]:
            - text: Username
            - textbox "Username" [ref=e14]:
              - /placeholder: Enter your username
              - text: invalid
          - generic [ref=e15]:
            - text: Password
            - textbox "Password" [ref=e16]:
              - /placeholder: Enter your password
              - text: wrong
          - button "Sign in" [ref=e17] [cursor=pointer]
        - generic [ref=e18]:
          - paragraph [ref=e19]: First time setup?
          - paragraph [ref=e20]:
            - text: Run
            - code [ref=e21]: python scripts/setup_admin.py
            - text: to create an admin user
  - alert [ref=e22]
```