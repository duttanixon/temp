"use client";

import { useState } from "react";
import { TabsNav } from "./TabsNav";
import { TabSelect } from "./TabSelect";
import { CustomerCreate } from "./CustomerCreate";
import { useCustomerFormBasic } from "@/app/(main)/customers/hooks/useCustomerForm";

export const CustomerForm = () => {
  const [activeTab, setActiveTab] = useState("basic");
  const basicForm = useCustomerFormBasic();

  return (
    <div className="flex flex-col gap-4">
      <div className="inline-flex w-fit border border-[#BDC3C7] rounded bg-[#FFFFFF] overflow-hidden">
        <TabsNav activeTab={activeTab} onChange={setActiveTab} />
      </div>
      <div className="w-230 h-106 border border-[#BDC3C7] rounded bg-[#FFFFFF]">
        <TabSelect
          activeTab={activeTab}
          companyName={basicForm.companyName}
          setCompanyName={basicForm.setCompanyName}
          email={basicForm.email}
          setEmail={basicForm.setEmail}
          address={basicForm.address}
          setAddress={basicForm.setAddress}
        />
      </div>
      <>
        <CustomerCreate {...basicForm} />
      </>
    </div>
  );
};
