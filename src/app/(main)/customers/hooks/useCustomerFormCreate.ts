import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { AxiosError } from "axios";
import { signOut } from "next-auth/react";

import { resetFormAfterDelay } from "@/app/(main)/customers/utils/resetFormAfterDelay";

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
  const [completedMessage, setCompletedMessage] = useState("");

  const router = useRouter();

  // 顧客データ作成APIを呼び出す関数
  const createCustomer = async (
    token: string
  ): Promise<CustomerResponse | null> => {
    const customerPayload = {
      name: companyName,
      contact_email: email,
      address: address,
      status: "ACTIVE",
    };

    const customerUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers`;

    try {
      const response = await axios.post(customerUrl, customerPayload, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });
      console.log("Registration complete:", response.data);
      setCompletedMessage("登録が完了しました");
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
      return response.data;
    } catch (error) {
      console.error("Registration error:", error);
      setCompletedMessage("");
      if (error instanceof AxiosError) {
        const status = error.response?.status;
        const detail = error.response?.data?.detail || "";
        console.error("登録エラー詳細:", error.response?.data);

        setErrorMessage(
          status === 400
            ? typeof detail === "string" && detail.includes("already exists")
              ? "既に登録されています"
              : "不正なリクエストです (Bad Request) "
            : status === 403
              ? "権限がありません (Forbidden)"
              : status === 422
                ? "入力値が正しくありません (Validation Error) "
                : "顧客データの作成に失敗しました"
        );
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
      return null;
    }
  };

  const handleCreate = async (): Promise<void> => {
    try {
      await createCustomer(token);
      console.log(token);
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
    completedMessage,
    setCompletedMessage,
    handleCreate,
    handleCancel,
    handleSubmit,
  };
};
