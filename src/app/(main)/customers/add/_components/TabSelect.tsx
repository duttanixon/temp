import { BasicTabContent } from "./BasicTabContent";
import { SubscriptionTabContent } from "./SubscriptionTabContent";

type Props = {
  activeTab: string;
  companyName: string;
  setCompanyName: (val: string) => void;
  email: string;
  setEmail: (val: string) => void;
  address: string;
  setAddress: (val: string) => void;
};

export const TabSelect = ({
  activeTab,
  companyName,
  setCompanyName,
  email,
  setEmail,
  address,
  setAddress,
}: Props) => {
  switch (activeTab) {
    case "basic":
      return (
        <BasicTabContent
          companyName={companyName}
          setCompanyName={setCompanyName}
          email={email}
          setEmail={setEmail}
          address={address}
          setAddress={setAddress}
        />
      );
    case "subscription":
      return <SubscriptionTabContent />;
    default:
      return null;
  }
};
