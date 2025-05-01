import { BasicTab } from "./BasicTabContent";
import { SubscriptionTab } from "./SubscriptionTabContent";

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
        <BasicTab
          companyName={companyName}
          setCompanyName={setCompanyName}
          email={email}
          setEmail={setEmail}
          address={address}
          setAddress={setAddress}
        />
      );
    case "subscription":
      return <SubscriptionTab />;
    default:
      return null;
  }
};
