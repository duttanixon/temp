"use client";

import { useState } from "react";
import { TabsNav } from "@/app/(main)/customers/_components/TabsNav";
import { TabSelect } from "@/app/(main)/customers/_components/TabSelect";
import { CustomerButton } from "@/app/(main)/customers/_components/CustomerButton";
import { useCustomerFormEdit } from "@/app/(main)/customers/hooks/useCustomerFormEdit";
import { useCustomerFormCreate } from "@/app/(main)/customers/hooks/useCustomerFormCreate";

type Props = {
  accessToken: string;
  customerId?: string;
};
export const CustomerForm = ({ accessToken, customerId }: Props) => {
  const [activeTab, setActiveTab] = useState("basic");
  const isEdit = !!customerId;
  const editForm = useCustomerFormEdit(accessToken, customerId!);
  const basicForm = useCustomerFormCreate(accessToken);
  const form = isEdit ? editForm : basicForm;

  if (form.errorMessage) {
    return (
      <div className="flex flex-col gap-8">
        <div className="text-red-500 text-2xl">
          <p>{form.errorMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="inline-flex w-fit border border-[#BDC3C7] rounded bg-[#FFFFFF] overflow-hidden">
        <TabsNav activeTab={activeTab} onChange={setActiveTab} />
      </div>
      <form onSubmit={form.handleSubmit} className="flex flex-col gap-4">
        <div className="w-230 h-106 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
          <TabSelect activeTab={activeTab} customerId={customerId} {...form} />
        </div>
        <CustomerButton isEdit={isEdit} {...form} />
      </form>
    </>
  );
};
