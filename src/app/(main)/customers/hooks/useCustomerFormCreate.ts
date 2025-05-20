import axios, { AxiosError } from "axios";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

type CustomerResponse = {
  id: string;
  name: string;
  contact_email: string;
  address: string;
  status: string;
};

export const useCustomerFormCreate = (token: string) => {
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const router = useRouter();

  // 顧客データ作成APIを呼び出す関数
  const createCustomer = async (
    token: string
  ): Promise<CustomerResponse | null> => {
    setErrorMessage("");
    try {
      if (!companyName || companyName.trim() === "") {
        setErrorMessage("会社名は必須項目です");
        return null;
      }
      if (!email || email.trim() === "") {
        setErrorMessage("連絡先メールアドレスは必須項目です");
        return null;
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (email && !emailRegex.test(email)) {
        setErrorMessage("有効なメールアドレスを入力してください");
        return null;
      }
      const customerPayload = {
        name: companyName,
        contact_email: email,
        address: address,
        status: "ACTIVE",
      };

      const customerUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers`;
      const response = await axios.post(customerUrl, customerPayload, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });
      console.log("Registration complete:", response.data);
      toast.success("顧客を追加しました");
      router.push(`/customers`);
      return response.data;
    } catch (error) {
      console.error("Registration error:", error);
      if (error instanceof AxiosError) {
        const status = error.response?.status;
        const detail = error.response?.data?.detail || "";
        console.error("登録エラー詳細:", error.response?.data);
        setErrorMessage(detail);
        if (status === 403) {
          signOut({ callbackUrl: "/login" }); // 自動ログアウト
        }
      }
      return null;
    }
  };

  const handleCreate = async (): Promise<void> => {
    try {
      await createCustomer(token);
    } catch (error) {
      console.error("Error:", error);
      setErrorMessage("error.message");
    }
  };

  // キャンセルボタン押下時の処理
  const handleCancel = (): void => {
    router.push("/customers");
  };

  // 作成ボタン押下時の処理
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    handleCreate();
  };

  return {
    companyName,
    setCompanyName,
    email,
    setEmail,
    address,
    setAddress,
    errorMessage,
    setErrorMessage,
    handleCreate,
    handleCancel,
    handleSubmit,
  };
};
