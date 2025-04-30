'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import AddCustomerModal from '@/app/(main)/customers/components/AddCustomerModal'

export default function AddCustomerButton() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        className="bg-green-600 hover:bg-green-700 text-white font-semibold"
        onClick={() => setOpen(true)}
      >
        + Add Customer
      </Button>
      <AddCustomerModal open={open} onOpenChange={setOpen} />
    </>
  )
}