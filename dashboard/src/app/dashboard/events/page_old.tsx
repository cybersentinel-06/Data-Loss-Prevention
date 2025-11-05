'use client'

import { useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { AlertTriangle, Usb, Clipboard, Cloud, Ban, Bell, Eye, Filter, Download } from 'lucide-react'

// Mock events data
const mockEvents = [
  {
    id: 1,
    timestamp: '2025-01-02 14:35:21',
    type: 'usb',
    severity: 'critical',
    action: 'blocked',
    agent: 'WIN-DESK-03',
    user: 'john.doe',
    description: 'Attempted to copy sensitive files to USB drive',
    details: 'File: financial_report_Q4.xlsx (Confidential)',
    deviceInfo: 'SanDisk USB 3.0 - 32GB'
  },
  {
    id: 2,
    timestamp: '2025-01-02 14:30:15',
    type: 'clipboard',
    severity: 'high',
    action: 'blocked',
    agent: 'UBUNTU-WS-02',
    user: 'jane.smith',
    description: 'Attempted to copy credit card numbers to clipboard',
    details: 'Content: 16 digit PAN detected (4111-****-****-1111)',
    deviceInfo: 'System Clipboard'
  },
  {
    id: 3,
    timestamp: '2025-01-02 14:25:42',
    type: 'cloud',
    severity: 'critical',
    action: 'blocked',
    agent: 'WIN-SRV-01',
    user: 'admin',
    description: 'Attempted to upload to Google Drive',
    details: 'File: customer_database.csv (Restricted)',
    deviceInfo: 'Google Drive'
  },
  {
    id: 4,
    timestamp: '2025-01-02 14:20:33',
    type: 'cloud',
    severity: 'medium',
    action: 'alerted',
    agent: 'MACOS-LAP-04',
    user: 'bob.johnson',
    description: 'Uploaded file to OneDrive',
    details: 'File: presentation.pptx (Internal)',
    deviceInfo: 'Microsoft OneDrive'
  },
  {
    id: 5,
    timestamp: '2025-01-02 14:15:18',
    type: 'usb',
    severity: 'high',
    action: 'quarantined',
    agent: 'WIN-DESK-03',
    user: 'sarah.williams',
    description: 'Attempted to copy multiple files to external drive',
    details: 'Files: 15 documents containing PII',
    deviceInfo: 'WD My Passport - 1TB'
  },
  {
    id: 6,
    timestamp: '2025-01-02 14:10:05',
    type: 'cloud',
    severity: 'critical',
    action: 'blocked',
    agent: 'RHEL-SRV-05',
    user: 'david.brown',
    description: 'Attempted to upload to Amazon S3',
    details: 'File: encryption_keys.txt (Secret)',
    deviceInfo: 'AWS S3 Bucket'
  },
  {
    id: 7,
    timestamp: '2025-01-02 14:05:50',
    type: 'clipboard',
    severity: 'medium',
    action: 'alerted',
    agent: 'WIN-DESK-03',
    user: 'emily.davis',
    description: 'Copied employee SSN to clipboard',
    details: 'Content: Social Security Number detected',
    deviceInfo: 'System Clipboard'
  },
  {
    id: 8,
    timestamp: '2025-01-02 14:00:25',
    type: 'cloud',
    severity: 'high',
    action: 'blocked',
    agent: 'UBUNTU-WS-02',
    user: 'michael.wilson',
    description: 'Attempted to upload to Dropbox',
    details: 'File: source_code.zip (Confidential)',
    deviceInfo: 'Dropbox'
  },
]

export default function EventsPage() {
  const [filter, setFilter] = useState('all')
  const [selectedEvent, setSelectedEvent] = useState<any>(null)

  const filteredEvents = filter === 'all'
    ? mockEvents
    : mockEvents.filter(e => e.type === filter)

  const stats = {
    total: mockEvents.length,
    usb: mockEvents.filter(e => e.type === 'usb').length,
    clipboard: mockEvents.filter(e => e.type === 'clipboard').length,
    cloud: mockEvents.filter(e => e.type === 'cloud').length,
    blocked: mockEvents.filter(e => e.action === 'blocked').length,
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'usb': return <Usb className="w-4 h-4" />
      case 'clipboard': return <Clipboard className="w-4 h-4" />
      case 'cloud': return <Cloud className="w-4 h-4" />
      default: return <AlertTriangle className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'usb': return 'text-blue-400 bg-blue-900/30 border-blue-500/50'
      case 'clipboard': return 'text-purple-400 bg-purple-900/30 border-purple-500/50'
      case 'cloud': return 'text-cyan-400 bg-cyan-900/30 border-cyan-500/50'
      default: return 'text-gray-400 bg-gray-900/30 border-gray-500/50'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-900/30 border-red-500/50'
      case 'high': return 'text-orange-400 bg-orange-900/30 border-orange-500/50'
      case 'medium': return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/50'
      case 'low': return 'text-green-400 bg-green-900/30 border-green-500/50'
      default: return 'text-gray-400 bg-gray-900/30 border-gray-500/50'
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'blocked': return 'text-red-400 bg-red-900/30 border-red-500/50'
      case 'quarantined': return 'text-orange-400 bg-orange-900/30 border-orange-500/50'
      case 'alerted': return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/50'
      default: return 'text-gray-400 bg-gray-900/30 border-gray-500/50'
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">DLP Events</h1>
            <p className="text-gray-400 mt-2">Monitor data loss prevention events across all endpoints</p>
          </div>
          <button className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-xl transition-colors">
            <Download className="w-5 h-5" />
            Export
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-xs">Total Events</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.total}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-gray-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-xs">USB Events</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">{stats.usb}</p>
              </div>
              <Usb className="w-10 h-10 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-xs">Clipboard</p>
                <p className="text-2xl font-bold text-purple-400 mt-1">{stats.clipboard}</p>
              </div>
              <Clipboard className="w-10 h-10 text-purple-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-xs">Cloud Storage</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">{stats.cloud}</p>
              </div>
              <Cloud className="w-10 h-10 text-cyan-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-xs">Blocked</p>
                <p className="text-2xl font-bold text-red-400 mt-1">{stats.blocked}</p>
              </div>
              <Ban className="w-10 h-10 text-red-400" />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            All Events
          </button>
          <button
            onClick={() => setFilter('usb')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'usb'
                ? 'bg-blue-900/50 text-blue-400 border border-blue-500/50'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <Usb className="w-4 h-4" />
            USB
          </button>
          <button
            onClick={() => setFilter('clipboard')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'clipboard'
                ? 'bg-purple-900/50 text-purple-400 border border-purple-500/50'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <Clipboard className="w-4 h-4" />
            Clipboard
          </button>
          <button
            onClick={() => setFilter('cloud')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'cloud'
                ? 'bg-cyan-900/50 text-cyan-400 border border-cyan-500/50'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <Cloud className="w-4 h-4" />
            Cloud Storage
          </button>
        </div>

        {/* Events List */}
        <div className="bg-gray-800/50 backdrop-blur-xl rounded-xl border border-gray-700/50 overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">Recent Events</h2>
          </div>
          <div className="divide-y divide-gray-700">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className="p-6 hover:bg-gray-700/30 transition-colors cursor-pointer"
                onClick={() => setSelectedEvent(event)}
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg border ${getTypeColor(event.type)}`}>
                    {getTypeIcon(event.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-white font-semibold">{event.description}</h3>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium ${getSeverityColor(event.severity)}`}>
                        {event.severity.toUpperCase()}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium ${getActionColor(event.action)}`}>
                        {event.action.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mb-2">{event.details}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>Agent: <span className="text-gray-400 font-medium">{event.agent}</span></span>
                      <span>User: <span className="text-gray-400 font-medium">{event.user}</span></span>
                      <span>Device: <span className="text-gray-400 font-medium">{event.deviceInfo}</span></span>
                      <span className="ml-auto">{event.timestamp}</span>
                    </div>
                  </div>
                  <button className="text-gray-400 hover:text-white transition-colors">
                    <Eye className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Event Details Modal */}
        {selectedEvent && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setSelectedEvent(null)}>
            <div className="bg-gray-800 rounded-2xl max-w-2xl w-full border border-gray-700" onClick={(e) => e.stopPropagation()}>
              <div className="p-6 border-b border-gray-700">
                <h3 className="text-2xl font-bold text-white">Event Details</h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="text-sm text-gray-400">Event ID</label>
                  <p className="text-white font-mono">#{selectedEvent.id}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Timestamp</label>
                  <p className="text-white">{selectedEvent.timestamp}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Type</label>
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border mt-1 ${getTypeColor(selectedEvent.type)}`}>
                    {getTypeIcon(selectedEvent.type)}
                    <span className="capitalize">{selectedEvent.type}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Description</label>
                  <p className="text-white">{selectedEvent.description}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Details</label>
                  <p className="text-white">{selectedEvent.details}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-400">Agent</label>
                    <p className="text-white font-medium">{selectedEvent.agent}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400">User</label>
                    <p className="text-white font-medium">{selectedEvent.user}</p>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Device Info</label>
                  <p className="text-white">{selectedEvent.deviceInfo}</p>
                </div>
                <div className="flex gap-3 pt-4">
                  <button onClick={() => setSelectedEvent(null)} className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg transition-colors">
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
