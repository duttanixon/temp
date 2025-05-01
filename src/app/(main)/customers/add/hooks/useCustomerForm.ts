import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { AxiosError } from "axios";

const password = process.env.NEXT_PUBLIC_ADMIN_PASSWORD ?? "";

type CustomerResponse = {
  id: string;
  name: string;
  contact_email: string;
  address: string;
  status: string;
};

export const useCustomerFormBasic = () => {
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [completedMessage, setCompletedMessage] = useState("");

  const router = useRouter();

  // フォームのリセットを行う関数
  const resetFormAfterDelay = (): void => {
    setTimeout(() => {
      setCompanyName("");
      setEmail("");
      setAddress("");
      setCompletedMessage("");
      setErrorMessage("");
    });
  };

  // アクセストークンを取得する関数
  const fetchAccessToken = async (): Promise<string> => {
    const formData = new URLSearchParams();
    formData.append("grant_type", "password");
    formData.append("username", email);
    formData.append("password", password);
    formData.append("scope", "");
    formData.append("client_id", "string");
    formData.append("client_secret", "string");
    console.log("email:", email);

    const loginUrl = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/auth/login`;

    try {
      const response = await axios.post(loginUrl, formData.toString(), {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Accept: "application/json",
        },
      });
      return response.data.access_token;
    } catch (error) {
      console.error("Login error:", error);
      if (error instanceof AxiosError) {
        const detail = error.response?.data?.detail || "Login failed";
        throw new Error(detail);
      }
      throw new Error("Unknown login error");
    }
  };

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
      resetFormAfterDelay();
      const response = await axios.post(customerUrl, customerPayload, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });
      console.log("Registration complete:", response.data);
      setCompletedMessage("登録が完了しました");
      return response.data;
    } catch (error) {
      console.error("Registration error:", error);
      setCompletedMessage("");
      if (error instanceof AxiosError) {
        const detail = error.response?.data?.detail || "";
        console.error("登録エラー詳細:", error.response?.data);
        setErrorMessage(
          typeof detail === "string" && detail.includes("already exists")
            ? "この会社名はすでに登録されています"
            : "顧客データの作成に失敗しました"
        );
      }
      return null;
    }
  };

  // 作成ボタン押下時の処理
  const handleCreate = async (): Promise<void> => {
    localStorage.removeItem("accessToken");
    localStorage.setItem("tokenResetDone", "true");

    // アクセストークンを持っているかの検証だが、上記のトークンリセットでトークンは消えているので、必ずトークンを取得する
    try {
      let token = localStorage.getItem("accessToken") || "";
      console.log("アクセストークン", token);
      if (!token) {
        token = await fetchAccessToken();
        console.log("アクセストークン", token);
        localStorage.setItem("accessToken", token);
      }
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
