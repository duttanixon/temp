import EditCustomerClient from "@/app/(main)/customers/[id]/edit/_components/EditCustomerClient";
import WithAccessToken from "@/app/(main)/customers/_components/WithAccessToken";

export default function AddCustomerPage() {
  return (
    <WithAccessToken>
      {(accessToken) => <EditCustomerClient accessToken={accessToken} />}
    </WithAccessToken>
  );
}
