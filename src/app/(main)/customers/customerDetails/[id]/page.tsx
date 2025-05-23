'use client'

import { useParams } from 'next/navigation';
import CustomerOverviewPage from '@/app/(main)/customers/customerDetails/[id]/CustomerOverviewPage';

export default function CustomerDetailsPage() {
  const { id } = useParams();
  return <CustomerOverviewPage customerId={id as string} />;
}