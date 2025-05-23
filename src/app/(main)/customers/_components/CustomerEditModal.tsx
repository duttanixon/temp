// File: app/(main)/customers/components/CustomerEditModal.tsx
'use client'

import { useState, useEffect } from 'react'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTitle,
  AlertDialogCancel
} from '@/components/ui/alert-dialog'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface Customer {
  customer_id: string
  name: string
  contact_email: string
  address: string
  status: string
  created_at: string
}

interface CustomerEditModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  customer: Customer | null
  onSubmit: (updatedCustomer: Customer) => void
}

export default function CustomerEditModal({ open, onOpenChange, customer, onSubmit }: CustomerEditModalProps) {
  const [form, setForm] = useState<Customer | null>(null)

  useEffect(() => {
    setForm(customer)
  }, [customer])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    if (!form) return
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async () => {
    if (!form) return

    try {
      const res = await fetch(`/api/customers/${form.customer_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          name: form.name,
          contact_email: form.contact_email,
          address: form.address,
          status: form.status
        })
      })

      if (!res.ok) throw new Error('Failed to update customer')

      const updated = await res.json()
      onSubmit(updated)
      onOpenChange(false)
    } catch (err) {
      console.error('Update error:', err)
    }
  }

  if (!form) return null

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogTitle className="sr-only">Edit Customer</AlertDialogTitle>
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Edit Customer</CardTitle>
                <CardDescription>Update customer information below</CardDescription>
              </div>
              <AlertDialogCancel className="text-sm">×</AlertDialogCancel>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input name="name" value={form.name} onChange={handleChange} placeholder="Customer Name" />
            <Input name="contact_email" type="email" value={form.contact_email} onChange={handleChange} placeholder="Contact Email" />
            <Input name="address" value={form.address} onChange={handleChange} placeholder="Address" />
            <select
              name="status"
              value={form.status}
              onChange={handleChange}
              className="border px-3 py-2 rounded w-full text-sm"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
            </select>
          </CardContent>
          <CardFooter>
            <Button className="w-full bg-blue-600 text-white" onClick={handleSubmit}>Save Changes</Button>
          </CardFooter>
        </Card>
      </AlertDialogContent>
    </AlertDialog>
  )
}
