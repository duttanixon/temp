"use client";

import { TabSelect } from "@/app/(main)/customers/_components/TabSelect";
import { CustomerButton } from "@/app/(main)/customers/_components/CustomerButton";
import { useCustomerFormEdit } from "@/app/(main)/customers/hooks/useCustomerFormEdit";
import { useCustomerFormCreate } from "@/app/(main)/customers/hooks/useCustomerFormCreate";

type Props = {
  accessToken: string;
  activeTab: string;
  customerId?: string;
};
export const CustomerForm = ({ accessToken, activeTab, customerId }: Props) => {
  const isEdit = !!customerId;
  const editForm = useCustomerFormEdit(accessToken, customerId!);
  const basicForm = useCustomerFormCreate(accessToken);
  const form = isEdit ? editForm : basicForm;

  return (
    <form onSubmit={form.handleSubmit} className="flex flex-col gap-4">
      <div className="w-230 h-106 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
        <TabSelect activeTab={activeTab} customerId={customerId} {...form} />
      </div>
      <CustomerButton isEdit={isEdit} {...form} />
    </form>
  );
};
