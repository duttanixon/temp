import CustomerHeader from '@/app/(main)/customers/customerDetails/[id]/CustomerHeader';
import CustomerTabs from '@/app/(main)/customers/customerDetails/[id]/CustomerTabs';
import CustomerStats from '@/app/(main)/customers/customerDetails/[id]/CustomerStats';
import CustomerProfile from '@/app/(main)/customers/customerDetails/[id]/CustomerProfile';
import RecentActivity from '@/app/(main)/customers/customerDetails/[id]/RecentActivity';

interface Props {
  customerId: string;
}

export default function CustomerOverviewPage({ customerId }: Props) {
  // You can fetch customer data using customerId here later
  return (
    <div className="p-6 space-y-6">
      <CustomerHeader name="Tokyo Metro" customerId={customerId} status="Active" />
      <CustomerTabs />
      <CustomerStats />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-end">
        <div className="md:col-span-2">
          <CustomerProfile />
        </div>
        <RecentActivity />
      </div>
    </div>
  );
}