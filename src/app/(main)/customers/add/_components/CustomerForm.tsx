"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useState } from "react";
import axios from "axios";
import { cva } from "class-variance-authority";

export const tagVariants = cva("text-sm font-normal text-[#7F8C8D]", {
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

  const resetFormAfterDelay = (delay: number = 2000) => {
    setTimeout(() => {
      setCompanyName("");
      setEmail("");
      setAddress("");
      setCompletedMessage("");
      setErrorMessage("");
    }, delay);
  };

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
      setCompletedMessage(""); // Clear success message on error
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
  const handleCreate = async () => {
    localStorage.removeItem("accessToken"); // トークンリセット
    localStorage.setItem("tokenResetDone", "true"); // フラグを立てる
    try {
      let token = localStorage.getItem("accessToken") || "";
      console.log("アクセストークン", token);
      if (!token) {
        token = await fetchAccessToken();
        console.log("アクセストークン", token);
        if (!token) {
          setErrorMessage(
            "アクセストークンが見つかりません。ログインしてください。"
          );
          return;
        }
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
    <div className="bg-[#FFFFFF] border border-[#BDC3C7] rounded w-full h-[577.8px]">
      <Tabs defaultValue="basic">
        <TabsList className="bg-[#FFFFFF] border-b-2 border-[#ECF0F1] rounded mb-4 space-x-2 w-full h-[44.4px] shadow-none">
          <TabsTrigger value="basic" className={tagVariants()}>
            Basic Info
          </TabsTrigger>
          <TabsTrigger value="contact" className={tagVariants()}>
            Contact
          </TabsTrigger>
          <TabsTrigger value="subscription" className={tagVariants()}>
            Subscription
          </TabsTrigger>
          <TabsTrigger value="users" className={tagVariants()}>
            Users
          </TabsTrigger>
          <TabsTrigger value="solutions" className={tagVariants()}>
            Solutions
          </TabsTrigger>
          <TabsTrigger value="settings" className={tagVariants()}>
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4 p-4">
          <h2 className="text-[#2C3E50] font-bold text-lg">
            Company Information
          </h2>
          <div className="flex flex-col gap-5 pt-4">
            <div>
              <Label htmlFor="companyName" className={labelStyle()}>
                Company Name *
              </Label>
              <Input
                className={inputStyle()}
                id="companyName"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="email" className={labelStyle()}>
                Contact Email *
              </Label>
              <Input
                className={inputStyle()}
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="address" className={labelStyle()}>
                Address
              </Label>
              <Input
                className={inputStyle()}
                id="address"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>
          </div>
          <div className="py-30">
            <div className="flex gap-2 pt-4">
              <Button
                className="w-[140px] bg-[#27AE60] hover:bg-[#27AE60] active:bg-[#27AE60] focus:bg-[#27AE60] text-[#FFFFFF]"
                variant="default"
                onClick={handleCreate}
              >
                Create
              </Button>
              <Button
                className="w-[140px] bg-[#BDC3C7] hover:bg-[#BDC3C7] active:bg-[#BDC3C7] focus:bg-[#BDC3C7] focus:text-[#7F8C8D]"
                variant="outline"
                disabled
              >
                Cancel
              </Button>
              <Button
                className="w-[250px] bg-[#3498DB] hover:bg-[#3498DB] active:bg-[#3498DB] focus:bg-[#3498DB] text-[#FFFFFF]"
                variant="secondary"
                disabled
              >
                Create & Configure Solutions
              </Button>
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
