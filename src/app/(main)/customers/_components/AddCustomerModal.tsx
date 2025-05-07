// File: app/(main)/customers/components/AddCustomerModal.tsx
'use client'

import { useState } from 'react'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTitle,
  AlertDialogCancel
} from '@/components/ui/alert-dialog'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '@/components/ui/card'

interface AddCustomerModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function AddCustomerModal({ open, onOpenChange }: AddCustomerModalProps) {
  const [form, setForm] = useState({
    name: '',
    contact_email: '',
    address: '',
    status: 'ACTIVE'
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async () => {
    try {
      const res = await fetch('/api/customers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(form)
      })

      if (!res.ok) throw new Error('Failed to create customer')

      const data = await res.json()
      console.log('Customer created:', data)
      onOpenChange(false)
    } catch (error) {
      console.error('Submit error:', error)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogTitle className="sr-only">Add New Customer</AlertDialogTitle>
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Add New Customer</CardTitle>
                <CardDescription>Fill in the details below to add a new customer.</CardDescription>
              </div>
              <AlertDialogCancel className="px-4 py-2 border rounded text-sm">×</AlertDialogCancel>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            <Input
              name="name"
              placeholder="Customer Name"
              value={form.name}
              onChange={handleChange}
            />
            <Input
              name="contact_email"
              type="email"
              placeholder="Contact Email"
              value={form.contact_email}
              onChange={handleChange}
            />
            <Input
              name="address"
              placeholder="Address"
              value={form.address}
              onChange={handleChange}
            />
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

          <CardFooter className="flex justify-between">
            <Button className="bg-green-600 text-white" onClick={handleSubmit}>
              Submit
            </Button>
          </CardFooter>
        </Card>
      </AlertDialogContent>
    </AlertDialog>
  )
}