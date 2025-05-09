import { useEffect, useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";
import { AxiosError } from "axios";
import { signOut } from "next-auth/react";
import { resetFormAfterDelay } from "@/app/(main)/customers/utils/resetFormAfterDelay";

export const useCustomerFormEdit = (
  accessToken: string,
  customerId: string
) => {
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [status, setStatus] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [completedMessage, setCompletedMessage] = useState("");

  const router = useRouter();

  useEffect(() => {
    if (!accessToken || !customerId) {
      console.log("useEffectスキップ: accessTokenかcustomerIdが未定義");
      return;
    }
    const fetchCustomer = async () => {
      try {
        const res = await axios.get(
          `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${customerId}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );
        console.log(
          "URL:",
          `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${customerId}`
        );
        console.log("アクセストークン:", accessToken);
        const data = res.data;
        console.log("data:", data);
        setCompanyName(data.name);
        setEmail(data.contact_email);
        setAddress(data.address);
        setStatus(data.status);
      } catch (err) {
        setErrorMessage("顧客情報の取得に失敗しました");
        console.log(err);
      }
    };
    if (accessToken && customerId) fetchCustomer();
  }, [accessToken, customerId]);

  const handleUpdate = async (): Promise<void> => {
    try {
      const payload = {
        name: companyName,
        contact_email: email,
        address,
        status,
      };
      const res = await axios.put(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${customerId}`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
        }
      );
      if (res.status === 200) {
        // setCompletedMessage("更新が完了しました");
        resetFormAfterDelay(
          {
            clearName: true,
            clearEmail: true,
            clearAddress: true,
            clearCompletedMessage: true,
            clearErrorMessage: true,
          },
          {
            setCompanyName,
            setEmail,
            setAddress,
            setCompletedMessage,
            setErrorMessage,
          }
        );
        router.push(`/customers/${customerId}`);
      }
    } catch (error) {
      setErrorMessage("更新に失敗しました");
      console.error(error);
      if (error instanceof AxiosError) {
        const status = error.response?.status;
        if (status === 403) {
          signOut({ callbackUrl: "/login" }); // 自動ログアウト
        }
      }
      resetFormAfterDelay(
        { clearErrorMessage: true },
        {
          setCompanyName,
          setEmail,
          setAddress,
          setCompletedMessage,
          setErrorMessage,
        }
      );
    }
  };

  const handleCancel = (): void => {
    router.push("/customers");
  };
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    handleUpdate();
  };
  return {
    companyName,
    setCompanyName,
    email,
    setEmail,
    address,
    setAddress,
    status,
    setStatus,
    errorMessage,
    setErrorMessage,
    completedMessage,
    setCompletedMessage,
    handleSubmit,
    handleCancel,
  };
};
