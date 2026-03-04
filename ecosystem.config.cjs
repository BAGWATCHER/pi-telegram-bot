module.exports = {
  apps: [{
    name: "pi-bot",
    script: "npm",
    args: "start",
    cwd: "/path/to/bot",
    restart_delay: 30000,
    max_restarts: 10,
    env: {
      NODE_ENV: "production",
    }
  }]
};
