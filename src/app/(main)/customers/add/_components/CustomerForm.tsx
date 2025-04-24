"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useState } from "react";
import axios from "axios";
import { cva } from "class-variance-authority";

export const tabVariants = cva("text-sm font-normal text-[#7F8C8D] h-full", {
  variants: {
    state: {
      active:
        "data-[state=active]:text-[#FFFFFF] data-[state=active]:bg-[#3498DB]",
    },
  },
  defaultVariants: {
    state: "active",
  },
});
export const labelStyle = cva("text-[#7F8C8D] text-sm font-normal");
export const inputStyle = cva("w-100 h-[35.56px] border-[#BDC3C7]");

export const CustomerForm = () => {
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [completedMessage, setCompletedMessage] = useState("");
  const password = process.env.NEXT_PUBLIC_ADMIN_PASSWORD ?? "";
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
        className={`text-sm mt-2 ${
          type === "success" ? "text-green-500" : "text-red-500"
        }`}
      >
        {message}
      </div>
    );
  };
  // フォームのリセットを行う関数
  const resetFormAfterDelay = (delay: number = 2000) => {
    setTimeout(() => {
      setCompanyName("");
      setEmail("");
      setAddress("");
      setCompletedMessage("");
      setErrorMessage("");
    }, delay);
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
      const response = await axios.post(customerUrl, customerPayload, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });
      console.log("Registration complete:", response.data);
      setCompletedMessage("登録が完了しました");
      resetFormAfterDelay(2000);
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
        resetFormAfterDelay(2000);
        return;
      }
    }
    resetFormAfterDelay(2000);
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
      resetFormAfterDelay(2000);
    }
  };
  return (
    <div className="bg-[#FFFFFF] border border-[#BDC3C7] rounded w-full h-full">
      <Tabs defaultValue="basic">
        <TabsList className="bg-[#FFFFFF] border-b-2 border-[#ECF0F1] rounded mb-4 space-x-2 w-full h-[44.4px] shadow-none">
          <TabsTrigger value="basic" className={tabVariants()}>
            基本情報
          </TabsTrigger>
          <TabsTrigger value="contact" className={tabVariants()}>
            連絡先
          </TabsTrigger>
          <TabsTrigger value="subscription" className={tabVariants()}>
            サブスクリプション
          </TabsTrigger>
          <TabsTrigger value="users" className={tabVariants()}>
            ユーザー
          </TabsTrigger>
          <TabsTrigger value="solutions" className={tabVariants()}>
            ソリューション
          </TabsTrigger>
          <TabsTrigger value="settings" className={tabVariants()}>
            設定
          </TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4 pl-8">
          <h2 className="text-[#2C3E50] font-bold text-lg">会社情報</h2>
          <div className="flex flex-col gap-5 pt-4">
            <>
              <Label htmlFor="companyName" className={labelStyle()}>
                会社名 *
              </Label>
              <Input
                className={inputStyle()}
                id="companyName"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </>
            <>
              <Label htmlFor="email" className={labelStyle()}>
                連絡先メール *
              </Label>
              <Input
                className={inputStyle()}
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </>
            <>
              <Label htmlFor="address" className={labelStyle()}>
                住所
              </Label>
              <Input
                className={inputStyle()}
                id="address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </>
          </div>
          <div className="pt-30 pb-10">
            <div className="flex gap-2 text-sm">
              <Button
                className="w-[140px] bg-[#27AE60] hover:bg-[#27AE60] active:bg-[#27AE60] focus:bg-[#27AE60] text-[#FFFFFF]"
                variant="default"
                onClick={handleCreate}
              >
                作成
              </Button>
              <Button
                className="w-[140px] bg-[#BDC3C7] hover:bg-[#BDC3C7] active:bg-[#BDC3C7] focus:bg-[#BDC3C7] focus:text-[#7F8C8D]"
                variant="outline"
                disabled
              >
                キャンセル
              </Button>
              <Button
                className="w-[250px] bg-[#3498DB] hover:bg-[#3498DB] active:bg-[#3498DB] focus:bg-[#3498DB] text-[#FFFFFF]"
                variant="secondary"
                disabled
              >
                作成 & ソリューション設定
              </Button>
              <p className="p-5 text-[#7F8C8D]">* 必須項目</p>
            </div>
            {completedMessage && !errorMessage && (
              <Message message={completedMessage} type="success" />
            )}
            {errorMessage && <Message message={errorMessage} type="error" />}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
