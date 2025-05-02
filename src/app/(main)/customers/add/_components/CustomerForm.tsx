"use client";

import { TabSelect } from "./TabSelect";
import { CustomerCreate } from "./CustomerCreate";
import { useCustomerFormBasic } from "@/app/(main)/customers/add/hooks/useCustomerForm";

type Props = {
  activeTab: string;
};
export const CustomerForm = ({ activeTab }: Props) => {
  const basicForm = useCustomerFormBasic();

  return (
    <form onSubmit={basicForm.handleSubmit} className="flex flex-col gap-4">
      <div className="w-230 h-106 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
        <TabSelect activeTab={activeTab} {...basicForm} />
      </div>
      <CustomerCreate {...basicForm} />
    </form>
  );
};
