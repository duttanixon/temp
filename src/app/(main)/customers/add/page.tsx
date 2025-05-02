import { auth } from "@/auth";
import AddCustomerClient from "./_components/AddCustomerClient";

export default async function AddCustomerPage() {
    const session = await auth();
    const accessToken = session?.accessToken ?? "";

    return <AddCustomerClient accessToken={accessToken} />;
}
