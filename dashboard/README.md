# CyberSentinel DLP Dashboard

Modern React dashboard for the CyberSentinel Data Loss Prevention system. Built with Vite, React, TypeScript, and Tailwind CSS.

## Features

- 📊 **Real-time Monitoring** - Live agent status and event tracking
- 🔍 **KQL Search** - Full Kibana Query Language support for advanced filtering
- 📈 **Visualizations** - Interactive charts for events, severity, and types
- 🎨 **Wazuh-Style UI** - Professional security dashboard design
- ⚡ **Fast & Modern** - Vite for lightning-fast development
- 🔒 **Secure** - JWT authentication with token refresh
- 📱 **Responsive** - Works on desktop, tablet, and mobile

## Tech Stack

- **Framework:** React 18
- **Build Tool:** Vite 5
- **Language:** TypeScript
- **Styling:** Tailwind CSS 3
- **Routing:** React Router v6
- **State Management:** TanStack React Query
- **Charts:** Recharts
- **Icons:** Lucide React
- **HTTP Client:** Axios

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- CyberSentinel Manager API running at `http://localhost:55000`

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The dashboard will be available at `http://localhost:3000`

## Project Structure

```
dashboard/
├── src/
│   ├── components/        # Reusable React components
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── StatsCard.tsx
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorMessage.tsx
│   │
│   ├── pages/             # Page components
│   │   ├── Dashboard.tsx  # Overview with charts
│   │   ├── Agents.tsx     # Agent management
│   │   ├── Events.tsx     # Event browser with KQL
│   │   ├── Alerts.tsx     # Alert management
│   │   ├── Policies.tsx   # Policy configuration
│   │   └── Settings.tsx   # System settings
│   │
│   ├── lib/               # Utilities and API client
│   │   ├── api.ts         # Backend API functions
│   │   └── utils.ts       # Helper functions
│   │
│   ├── App.tsx            # Root component with routing
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
│
├── public/                # Static assets
├── index.html             # HTML template
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
└── package.json           # Dependencies
```

## Configuration

### API Endpoint

Configure the backend API URL in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:55000',
        changeOrigin: true,
      },
    },
  },
})
```

Or set the environment variable:

```bash
VITE_API_URL=http://your-api-url:55000
```

### Tailwind Colors

Customize the color scheme in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* Your brand colors */ },
      sidebar: { bg: '#1a1d1f', hover: '#2a2d2f' },
      status: { active: '#00b050', inactive: '#e74c3c' },
    },
  },
}
```

## Pages

### Dashboard
- Overview statistics (agents, events, alerts)
- Time-series chart (events over time)
- Pie chart (events by type)
- Bar chart (events by severity)
- DLP actions summary

### Agents
- Real-time agent status monitoring
- Agent list with details (OS, IP, last seen)
- Status indicators (active, inactive, pending)
- Agent deletion
- Auto-refresh every 10 seconds

### Events
- **KQL Search** - Full Kibana Query Language support
  ```
  Examples:
  event.type:file
  event.severity:critical
  blocked:true
  event.type:file AND event.severity:high
  ```
- Quick filters (Critical, Blocked, File, USB, Clipboard)
- Event details modal
- Classification labels
- Policy match indicators
- Auto-refresh every 15 seconds

### Alerts
- Alert list with status (new, acknowledged, resolved)
- Severity indicators
- Acknowledge/resolve actions
- Alert statistics

### Policies
- Example policies (PCI-DSS, GDPR, HIPAA, USB)
- Policy creation guide with YAML template
- Status and priority display

### Settings
- System configuration
- OpenSearch settings
- Notification preferences
- About information

## KQL (Kibana Query Language)

The Events page supports full KQL syntax for powerful search:

### Basic Syntax
```
field:value                    # Exact match
field:"exact phrase"           # Phrase match
field:*wildcard*              # Wildcard match
field > 100                   # Comparison
field:(value1 OR value2)      # Multiple values
NOT field:value               # Negation
```

### Examples
```
# Find critical file events
event.type:file AND event.severity:critical

# Find blocked events
blocked:true

# Find events from specific agent
agent.id:AGENT-0001

# Find events with classifications
classification:*

# Find PDF files
file.extension:.pdf

# Complex query
event.type:file AND event.severity:(high OR critical) AND NOT blocked:false
```

## API Integration

The dashboard communicates with the FastAPI backend:

```typescript
import { getAgents, searchEvents, getStats } from '@/lib/api'

// Fetch agents
const agents = await getAgents()

// Search events with KQL
const results = await searchEvents('event.type:file', {
  size: 100,
  start_date: '2025-01-01',
})

// Get dashboard stats
const stats = await getStats()
```

## Development

### Hot Module Replacement (HMR)
Vite provides instant HMR - changes appear immediately in the browser.

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

### Building
```bash
npm run build
# Output in dist/
```

## Deployment

### Docker

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
server {
  listen 80;
  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }
  location /api {
    proxy_pass http://manager:55000;
    proxy_set_header Host $host;
  }
}
```

## Customization

### Adding a New Page

1. Create page component in `src/pages/`:
```typescript
// src/pages/MyPage.tsx
export default function MyPage() {
  return <div>My Page Content</div>
}
```

2. Add route in `src/App.tsx`:
```typescript
<Route path="mypage" element={<MyPage />} />
```

3. Add navigation in `src/components/Sidebar.tsx`:
```typescript
{ name: 'My Page', to: '/mypage', icon: Icon }
```

### Adding a Chart

```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'

<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <XAxis dataKey="timestamp" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="value" stroke="#3b82f6" />
  </LineChart>
</ResponsiveContainer>
```

## Troubleshooting

### API Connection Issues
- Check that the backend is running at `http://localhost:55000`
- Verify proxy configuration in `vite.config.ts`
- Check browser console for CORS errors

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`
- Check TypeScript errors: `npm run type-check`

### Hot Reload Not Working
- Restart dev server
- Check for syntax errors in components
- Ensure files are inside `src/` directory

## Performance

- **React Query** - Smart caching with automatic background refetching
- **Code Splitting** - Route-based lazy loading (future)
- **Tree Shaking** - Vite removes unused code
- **Asset Optimization** - Automatic minification and compression

## Security

- **JWT Authentication** - Tokens stored in memory (not localStorage)
- **HTTPS** - Use HTTPS in production
- **CSP Headers** - Configure Content Security Policy
- **Input Validation** - All user inputs sanitized

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting
5. Commit: `git commit -m 'Add my feature'`
6. Push: `git push origin feature/my-feature`
7. Create a Pull Request

## License

Apache 2.0 - See LICENSE file

## Support

- Documentation: [docs.cybersentinel.com](https://docs.cybersentinel.com)
- Issues: [GitHub Issues](https://github.com/your-org/cybersentinel-dlp/issues)
- Email: support@cybersentinel.com

---

**Version:** 2.0.0
**Last Updated:** 2025-01-12
**Project:** CyberSentinel DLP
