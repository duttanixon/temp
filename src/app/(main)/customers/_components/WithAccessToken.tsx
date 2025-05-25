import { auth } from "@/auth";

type Props = {
  children: (accessToken: string) => React.ReactNode;
};

export default async function WithAccessToken({ children }: Props) {
  const session = await auth();
  const accessToken = session?.accessToken ?? "";
  return <>{children(accessToken)}</>;
}
