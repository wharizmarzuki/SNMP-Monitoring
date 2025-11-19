/**
 * PM2 Ecosystem Configuration for SNMP Monitoring System
 *
 * Usage:
 *   Start:    pm2 start ecosystem.config.js
 *   Stop:     pm2 stop ecosystem.config.js
 *   Restart:  pm2 restart ecosystem.config.js
 *   Monitor:  pm2 monit
 *   Logs:     pm2 logs
 *   Status:   pm2 status
 */

module.exports = {
  apps: [
    {
      name: 'snmp-backend',
      cwd: './backend',
      script: 'venv/bin/uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8000',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      env_production: {
        NODE_ENV: 'production',
      },
      error_file: './logs/pm2-backend-error.log',
      out_file: './logs/pm2-backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
    },
    {
      name: 'snmp-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:8000',
      },
      error_file: './logs/pm2-frontend-error.log',
      out_file: './logs/pm2-frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
    },
  ],
};
