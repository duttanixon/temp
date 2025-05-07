// File: app/(main)/customers/components/CustomerDetailModal.tsx
'use client'

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
  CardContent
} from '@/components/ui/card'

interface CustomerDetailModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  customer: {
    name: string
    contact_email: string
    address: string
    status: string
    created_at: string
  } | null
}

export default function CustomerDetailModal({ open, onOpenChange, customer }: CustomerDetailModalProps) {
  if (!customer) return null

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogTitle className="sr-only">Customer Detail View</AlertDialogTitle>
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>{customer.name}</CardTitle>
                <CardDescription>Customer Detail View</CardDescription>
              </div>
              <AlertDialogCancel className="text-sm">×</AlertDialogCancel>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div><strong>Email:</strong> {customer.contact_email}</div>
            <div><strong>Address:</strong> {customer.address}</div>
            <div><strong>Status:</strong> {customer.status}</div>
            <div><strong>Created On:</strong> {new Date(customer.created_at).toLocaleDateString()}</div>
          </CardContent>
        </Card>
      </AlertDialogContent>
    </AlertDialog>
  )
}
