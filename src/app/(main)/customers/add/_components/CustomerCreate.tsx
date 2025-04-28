import axios from "axios";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  companyName: string;
  email: string;
  address: string;
  setCompanyName: (val: string) => void;
  setEmail: (val: string) => void;
  setAddress: (val: string) => void;
  completedMessage: string;
  setCompletedMessage: (val: string) => void;
  errorMessage: string;
  setErrorMessage: (val: string) => void;
};
const password = process.env.NEXT_PUBLIC_ADMIN_PASSWORD ?? "";
export const CustomerCreate = ({
  companyName,
  email,
  address,
  setCompanyName,
  setEmail,
  setAddress,
  completedMessage,
  setCompletedMessage,
  errorMessage,
  setErrorMessage,
}: Props) => {
  const router = useRouter();
  // 顧客作成可否のメッセージを表示
  const Message = ({
    message,
    type,
  }: {
    message: string;
    type: "success" | "error";
  }) => {
    return (
      <div
        className={cn(
          "text-sm",
          type === "success" ? "text-green-500" : "text-red-500"
        )}
      >
        {message}
      </div>
    );
  };
  // // フォームのリセットを行う関数
  const resetFormAfterDelay = () => {
    setTimeout(() => {
      setCompanyName("");
      setEmail("");
      setAddress("");
      setCompletedMessage("");
      setErrorMessage("");
    });
  };
  // アクセストークンを取得する関数
  const fetchAccessToken = async () => {
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
    } catch (error: any) {
      console.error("Login error:", error);
      const detail = error.response?.data?.detail || "Login failed";
      throw new Error(detail);
    }
  };
  // 顧客データ作成APIを呼び出す関数
  const createCustomer = async (token: string) => {
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
    } catch (error: any) {
      console.error("Registration error:", error);
      setCompletedMessage("");
      const detail = error.response?.data?.detail || "";
      console.error("登録エラー詳細:", error.response?.data);
      setErrorMessage(
        typeof detail === "string" && detail.includes("already exists")
          ? "この会社名はすでに登録されています"
          : "顧客データの作成に失敗しました"
      );
      if (!companyName || !email || !password) {
        setErrorMessage("全ての必須項目を入力してください");
        return;
      }
    }
  };
  // 作成ボタン押下時の処理
  const handleCreate = async () => {
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
  const handleCancel = () => {
    router.push("/customers");
  };
  return (
    <>
      <div className="flex gap-2">
        <Button
          className="w-[140px] bg-[#27AE60] text-[#FFFFFF] hover:bg-[#27AE60] active:bg-[#27AE60] focus:bg-[#27AE60] text-sm font-normal cursor-pointer"
          variant="default"
          onClick={handleCreate}
        >
          作成
        </Button>
        <Button
          className="w-[140px] bg-[#BDC3C7] text-[#7F8C8D] hover:bg-[#BDC3C7] active:bg-[#BDC3C7] focus:bg-[#BDC3C7] text-sm font-normal cursor-pointer"
          variant="outline"
          onClick={handleCancel}
        >
          キャンセル
        </Button>
      </div>
      {completedMessage && !errorMessage && (
        <Message message={completedMessage} type="success" />
      )}
      {errorMessage && <Message message={errorMessage} type="error" />}
    </>
  );
};
