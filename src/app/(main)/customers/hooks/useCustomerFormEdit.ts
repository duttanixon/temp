import axios, { AxiosError } from "axios";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
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
        setErrorMessage("顧客情報の取得に失敗しました");
        console.log(err);
      }
    };
    if (accessToken && customerId) fetchCustomer();
  }, [accessToken, customerId]);

  const handleUpdate = async (): Promise<void> => {
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
          setErrorMessage(
            status === 400
              ? typeof detail === "string" &&
                detail.includes("name already exists")
                ? "会社名が既に登録されています"
                : typeof detail === "string" &&
                    detail.includes("email already exists")
                  ? "連絡先メールアドレスが既に登録されています"
                  : "重複しています"
              : ""
          );
        }
      }
    }
  };

  const handleCancel = (): void => {
    router.push(`/customers/${customerId}`);
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
    handleSubmit,
    handleCancel,
  };
};
