'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

export default function EditCustomerPage() {
  const { id } = useParams()
  const router = useRouter()

  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    name: '',
    businessType: '',
    contactEmail: '',
    contactPhone: '',
    address: '',
    status: 'ACTIVE',
  })

  useEffect(() => {
    const fetchCustomer = async () => {
      try {
        const res = await fetch(`/api/customers/${id}`)
        if (!res.ok) throw new Error('Failed to fetch')
        const data = await res.json()

        setForm({
          name: data.name || '',
          businessType: data.business_type || '',
          contactEmail: data.contact_email || '',
          contactPhone: data.contact_phone || '',
          address: data.address || '',
          status: data.status || 'ACTIVE',
        })
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchCustomer()
  }, [id])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSave = async () => {
    try {
      const res = await fetch(`/api/customers/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          name: form.name,
          business_type: form.businessType,
          contact_email: form.contactEmail,
          contact_phone: form.contactPhone,
          address: form.address,
          status: form.status,
        }),
      })

      if (!res.ok) throw new Error('Update failed')
      router.push(`/customers/customerDetails/${id}`)
    } catch (err) {
      console.error('Save error:', err)
    }
  }

  if (loading) return <div className="p-6">Loading...</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Edit Customer: {form.name}</h1>
      <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Label>Company Name *</Label>
              <Input name="name" value={form.name} onChange={handleChange} />
            </div>
            <div className="space-y-4">
              <Label>Business Type</Label>
              <Input name="businessType" value={form.businessType} onChange={handleChange} />
            </div>
          </div>

          <div className="flex flex-col md:flex-row gap-6">
            <div className="w-full md:w-1/2">
              <Label>Contact Email *</Label>
              <Input name="contactEmail" value={form.contactEmail} onChange={handleChange} />
            </div>
            <div className="w-full md:w-1/2">
              <Label>Contact Phone *</Label>
              <Input name="contactPhone" value={form.contactPhone} onChange={handleChange} />
            </div>
          </div>

          <div>
            <Label>Address</Label>
            <Textarea name="address" value={form.address} onChange={handleChange} rows={3} />
          </div>

          <div className="w-1/2">
            <Label>Status</Label>
            <select
              name="status"
              value={form.status}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-800 bg-white"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="PENDING">PENDING</option>
            </select>
          </div>
        </div>

        <div className="flex justify-start space-x-4 pt-4">
          <Button onClick={handleSave}>Save</Button>
          <Button variant="outline" onClick={() => router.back()}>Cancel</Button>
        </div>
      </div>
    </div>
  )
}