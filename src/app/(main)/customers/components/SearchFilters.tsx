// File: app/(main)/customers/components/SearchFilters.tsx
'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface SearchFiltersProps {
  onSearch: (query: string, status: string, region: string) => void
}

export default function SearchFilters({ onSearch }: SearchFiltersProps) {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('All Statuses')
  const [region, setRegion] = useState('All Regions')

  const handleSubmit = () => {
    onSearch(query.trim(), status, region)
  }

  return (
    <div className="flex flex-wrap gap-4 items-center">
      <select className="border px-3 py-2 rounded text-sm" value={status} onChange={e => setStatus(e.target.value)}>
        <option>All Statuses</option>
        <option>Active</option>
        <option>Suspended</option>
        <option>Inactive</option>
      </select>

      <select className="border px-3 py-2 rounded text-sm" value={region} onChange={e => setRegion(e.target.value)}>
        <option>All Regions</option>
        <option>Japan</option>
        <option>South Korea</option>
        <option>Singapore</option>
        <option>Thailand</option>
      </select>

      <Input
        placeholder="Search customers..."
        className="w-64"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <Button variant="outline" onClick={handleSubmit}>Search</Button>
    </div>
  )
}