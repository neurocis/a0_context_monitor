# Context Monitor Plugin

🔍 **Monitor AgentContext memory usage, creation/removal, and export context inventory.**

Provides REST API endpoints and a web dashboard for visibility into active contexts. **Monitoring only** — no automatic cleanup (for manual control).

## Features

- 📊 **Context Inventory**: List all active contexts with memory estimates
- 📈 **Summary Statistics**: Total contexts, memory usage, running vs. idle count
- 📝 **JSON Export**: Dump full context inventory to file for analysis
- 🌐 **REST API**: Query context state programmatically
- 📱 **Web Dashboard**: Real-time formatted table of all contexts
- 🔔 **Status Monitoring**: Check if context monitoring is available
- 📄 **Formatted Output**: Display human-readable context summary table

<img width="1122" height="664" alt="image" src="https://github.com/user-attachments/assets/6b372b47-3981-4292-973d-144222cc02a7" />

## Installation

The plugin is a **local plugin** installed in `/a0/usr/plugins/a0_context_monitor/`.

No additional installation steps required — it will be automatically discovered by the Agent Zero framework.

## Usage

### Web Dashboard

Open the dashboard from the plugin menu to view:

- **Stats Grid**: Total contexts, total memory, running contexts, idle contexts
- **Contexts Table**: Full inventory with ID, name, size, message count, status, creation time, last activity
- **Refresh Button**: Manually refresh data
- **Export Button**: Dump context inventory to JSON file

The dashboard auto-refreshes every 30 seconds.

### REST API Endpoints

All endpoints return JSON responses.

#### Get Monitoring Status

```bash
GET /api/context-monitor/status
```

Check if context monitoring is available.

**Response:**
```json
{
  "available": true,
  "message": "Context monitoring is available"
}
```

#### Get Context Inventory

```bash
GET /api/context-monitor/contexts?detailed=true
```

List all contexts with optional detailed information.

**Query Parameters:**
- `detailed` (bool): Include per-context details (default: `false`)

**Response:**
```json
{
  "total_contexts": 8,
  "total_estimated_size_mb": 45.23,
  "timestamp": "2026-04-17T22:33:33",
  "contexts": [
    {
      "id": "abc12def",
      "name": "chat_with_user",
      "type": "user",
      "estimated_size_mb": 5.67,
      "estimated_size_kb": 5824,
      "log_entries": 42,
      "log_updates": 15,
      "data_keys": 3,
      "is_running": true,
      "created_at": "2026-04-17T20:15:30",
      "last_message": "2026-04-17T22:25:45"
    }
  ]
}
```

#### Get Summary Statistics

```bash
GET /api/context-monitor/summary
```

Get aggregated context statistics.

**Response:**
```json
{
  "status": "success",
  "total_contexts": 8,
  "total_estimated_size_mb": 45.23,
  "running_contexts": 3,
  "idle_contexts": 5,
  "timestamp": "2026-04-17T22:33:33"
}
```

#### Get Context Details

```bash
GET /api/context-monitor/contexts/{context_id}
```

Get detailed information about a specific context.

**Path Parameters:**
- `context_id` (str): The context ID to look up

**Response:**
```json
{
  "context": {
    "id": "abc12def",
    "name": "chat_with_user",
    "type": "user",
    "estimated_size_mb": 5.67,
    "log_entries": 42,
    "is_running": true,
    "created_at": "2026-04-17T20:15:30",
    "last_message": "2026-04-17T22:25:45"
  },
  "found": true
}
```

#### Export Context Inventory

```bash
POST /api/context-monitor/export
```

Export context inventory to JSON file.

**Optional Request Body:**
```json
{
  "file_path": "/custom/path/to/contexts.json"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Context inventory exported successfully",
  "file_path": "/tmp/agent_contexts_inventory.json"
}
```

#### Get Summary Table

```bash
GET /api/context-monitor/table
```

Get formatted context summary as text.

**Response:**
```json
{
  "table": "Context Summary Table (formatted text)...",
  "status": "success"
}
```

## Integration Examples

### Python: Query Context Info

```python
import requests

response = requests.get('http://localhost:8000/api/context-monitor/summary')
summary = response.json()

print(f"Total contexts: {summary['total_contexts']}")
print(f"Total memory: {summary['total_estimated_size_mb']:.1f} MB")
print(f"Running: {summary['running_contexts']}, Idle: {summary['idle_contexts']}")
```

### JavaScript: Fetch Context Inventory

```javascript
async function getContexts() {
  const response = await fetch('/api/context-monitor/contexts?detailed=true');
  const data = await response.json();
  
  console.log(`Found ${data.total_contexts} contexts`);
  data.contexts.forEach(ctx => {
    console.log(`  ${ctx.name}: ${ctx.estimated_size_mb.toFixed(2)} MB`);
  });
}
```

### Bash: Export and Analyze

```bash
# Export context inventory
curl -X POST http://localhost:8000/api/context-monitor/export \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/tmp/my_contexts.json"}'

# Analyze with jq
jq '.contexts | length' /tmp/my_contexts.json
jq '.total_estimated_size_mb' /tmp/my_contexts.json
```

## Plugin Architecture

```
a0_context_monitor/
├── plugin.yaml              # Manifest
├── hooks.py                 # Lifecycle hooks
├── README.md                # This file
├── api/
│   └── context_monitor_api.py   # REST API handlers
├── helpers/
│   └── monitor.py           # Core monitoring logic
└── webui/
    ├── dashboard.html       # Web dashboard
    └── dashboard-store.js   # Alpine.js store (state management)
```

### How It Works

1. **helpers/monitor.py** (`ContextMonitorHelper`): Thin wrapper around existing `AgentContext` monitoring methods
   - Calls `AgentContext.get_contexts_info()` for inventory
   - Calls `AgentContext.dump_contexts_info()` for JSON export
   - Calls `AgentContext.display_contexts_summary()` for formatted output

2. **api/context_monitor_api.py** (`ContextMonitorApiHandler`): FastA2A REST endpoints
   - Uses `ContextMonitorHelper` to fetch data
   - Returns JSON responses

3. **webui/dashboard-store.js** (`contextMonitorStore`): Alpine.js Store Gate module
   - Manages dashboard state (loading, error, summary, contexts)
   - Calls REST API endpoints
   - Auto-refreshes every 30 seconds

4. **webui/dashboard.html**: Responsive web interface
   - Uses Alpine.js directives
   - Displays stats grid and contexts table
   - Buttons for refresh and export

## Monitoring Only

⚠️ **Important**: This plugin is **monitoring only** — it does NOT automatically remove or cleanup contexts.

- ✅ Logs context creation/removal (from `AgentContext`)
- ✅ Tracks memory usage estimates
- ✅ Exports context inventory as JSON
- ✅ Provides REST API for querying state
- ✅ Displays formatted context summary

- ❌ Does NOT automatically remove inactive contexts
- ❌ Does NOT implement automatic cleanup
- ❌ Does NOT limit context lifetime

For automatic cleanup, see the embedded `ContextMonitor` class in `/a0/agent.py`, which can be enabled separately.

## Troubleshooting

### "Context monitoring is not available" error

This means `AgentContext` is not properly initialized in the current runtime. Ensure:
1. Agent Zero framework is running
2. At least one agent context exists
3. The framework version supports `AgentContext` monitoring methods

### Empty contexts list

If the dashboard shows 0 contexts:
1. Create a new conversation or agent context
2. Refresh the dashboard
3. New contexts should appear after creation

### Export file not found

The default export path is `/tmp/agent_contexts_inventory.json`. Check:
1. `/tmp/` directory is writable
2. Provide a custom `file_path` in the export endpoint

## Performance Notes

- Memory estimation is rough (based on log entry count × average message size)
- Real memory usage may differ due to Python object overhead and garbage collection
- Dashboard auto-refresh every 30 seconds (configurable in `dashboard-store.js`)
- API calls are lightweight and do not modify state

## Related Documentation

- **AgentContext**: See `/a0/agent.py` for the underlying `AgentContext` class
- **ContextMonitor**: Embedded monitoring class in `/a0/agent.py` with cleanup capabilities
- **Plugin System**: See `/a0/docs/agents/AGENTS.plugins.md` for plugin architecture

## License

This plugin is part of Agent Zero and follows the same license as the framework.
