import { Bell, Search, User } from 'lucide-react'
import { useState } from 'react'

export default function Header() {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex-1 max-w-2xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search agents, events, alerts... (Use KQL)"
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4 ml-6">
        {/* Notifications */}
        <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
        </button>

        {/* User Menu */}
        <button className="flex items-center gap-2 p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <User className="h-5 w-5" />
          <span className="text-sm font-medium">Admin</span>
        </button>
      </div>
    </header>
  )
}
