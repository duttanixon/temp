import axios, { AxiosError } from "axios";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

export const useCustomerFormEdit = (
  accessToken: string,
  customerId: string
) => {
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [status, setStatus] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

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
        const data = res.data;
        setCompanyName(data.name);
        setEmail(data.contact_email);
        setAddress(data.address);
        setStatus(data.status);
      } catch (err) {
        console.log(err);
        const axiosError = err as AxiosError;
        if (axiosError.isAxiosError && axiosError.response) {
          const status = axiosError.response.status;
          if (status === 404 || status === 422) {
            setErrorMessage(
              `指定された顧客 (ID: ${customerId}) は存在しません。`
            );
          } else if (status === 403) {
            setErrorMessage(
              `この顧客を編集する権限がありません。ステータス: ${axiosError.response.status}`
            );
          } else {
            setErrorMessage(
              `顧客情報の取得に失敗しました。ステータス: ${axiosError.response.status}`
            );
          }
        }
      }
    };
    if (accessToken && customerId) fetchCustomer();
  }, [accessToken, customerId]);

  const handleUpdate = useCallback(async (): Promise<void> => {
    setErrorMessage("");
    try {
      if (!companyName || companyName.trim() === "") {
        setErrorMessage("会社名は必須項目です");
        return;
      }
      if (!email || email.trim() === "") {
        setErrorMessage("連絡先メールアドレスは必須項目です");
        return;
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (email && !emailRegex.test(email)) {
        setErrorMessage("有効なメールアドレスを入力してください");
        return;
      }
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
        toast.success("編集内容を保存しました");
        router.push(`/customers/${customerId}`);
      }
    } catch (error) {
      console.error(error);
      if (error instanceof AxiosError) {
        const status = error.response?.status;
        if (status === 403) {
          signOut({ callbackUrl: "/login" }); // 自動ログアウト
        }
        if (status === 400) {
          const detail = error.response?.data?.detail;
          console.error(detail);
          setErrorMessage(detail);
        }
      }
    }
  }, [companyName, email, address, status, accessToken, customerId, router]);

  const handleCancel = useCallback((): void => {
    router.push(`/customers/${customerId}`);
  }, [customerId, router]);
  const handleSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      handleUpdate();
    },
    [handleUpdate]
  );
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
    handleSubmit,
    handleCancel,
  };
};
