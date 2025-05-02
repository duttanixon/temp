import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { getServerSession } from "next-auth";
import AddCustomerClient from "./_components/AddCustomerClient";

export default async function AddCustomerPage() {
  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken ?? "";

  return <AddCustomerClient accessToken={accessToken} />;
}
