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
  const [status, setStatus] = useState('ステータスがすべてのステータス')
  const [region, setRegion] = useState('地域: すべての地域')

  const handleSubmit = () => {
    onSearch(query.trim(), status, region)
  }

  return (
    <div className="flex flex-wrap gap-4 items-center">
      <select className="border px-3 py-2 rounded text-sm" value={status} onChange={e => setStatus(e.target.value)}>
        <option>ステータスがすべてのステータス</option>
        <option>Active</option>
        <option>Suspended</option>
        <option>Inactive</option>
      </select>

      <select className="border px-3 py-2 rounded text-sm" value={region} onChange={e => setRegion(e.target.value)}>
        <option>地域: すべての地域</option>
        <option>Japan</option>
        <option>South Korea</option>
        <option>Singapore</option>
        <option>Thailand</option>
      </select>

      <Input
        placeholder="顧客を検索…"
        className="w-64"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <Button variant="outline" onClick={handleSubmit}>検査</Button>
    </div>
  )
}