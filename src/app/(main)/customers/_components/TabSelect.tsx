import { EditBasicTabContent } from "@/app/(main)/customers/[id]/edit/_components/EditBasicTabContent";
import { AddBasicTabContent } from "@/app/(main)/customers/add/_components/AddBasicTabContent";
import { EditSubscriptionTabContent } from "@/app/(main)/customers/[id]/edit/_components/EditSubscriptionTabContent";
import { AddSubscriptionTabContent } from "@/app/(main)/customers/add/_components/AddSubscriptionTabContent";

type Props = {
  activeTab: string;
  customerId?: string;
  companyName: string;
  setCompanyName: (val: string) => void;
  email: string;
  setEmail: (val: string) => void;
  address: string;
  setAddress: (val: string) => void;
  status?: string;
  setStatus?: (val: string) => void;
};

export const TabSelect = ({
  activeTab,
  customerId,
  companyName,
  setCompanyName,
  email,
  setEmail,
  address,
  setAddress,
  status,
  setStatus,
}: Props) => {
  switch (activeTab) {
    case "basic":
      return customerId ? (
        <EditBasicTabContent
          customerId={customerId}
          companyName={companyName}
          setCompanyName={setCompanyName}
          email={email}
          setEmail={setEmail}
          address={address}
          setAddress={setAddress}
          status={status ?? ""}
          setStatus={setStatus ?? (() => {})}
        />
      ) : (
        <AddBasicTabContent
          companyName={companyName}
          setCompanyName={setCompanyName}
          email={email}
          setEmail={setEmail}
          address={address}
          setAddress={setAddress}
        />
      );
    case "subscription":
      return customerId ? (
        <EditSubscriptionTabContent />
      ) : (
        <AddSubscriptionTabContent />
      );
    default:
      return null;
  }
};
