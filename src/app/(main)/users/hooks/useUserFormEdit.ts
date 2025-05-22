import axios, { AxiosError } from "axios";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";

export const useUserFormEdit = (
  accessToken: string,
  initialRole: string,
  userId: string
) => {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState(initialRole);
  const [customer, setCustomer] = useState("");
  const [status, setStatus] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const router = useRouter();

  useEffect(() => {
    if (!accessToken || !userId) {
      console.log("useEffectスキップ: accessTokenかuserIdが未定義");
      return;
    }
    const fetchUser = async () => {
      try {
        const res = await axios.get(
          `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/${userId}`,
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );
        const data = res.data;
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setEmail(data.email);
        setRole(data.role);
        setCustomer(data.customer_id);
        setStatus(data.status);
      } catch (err) {
        console.log(err);
        const axiosError = err as AxiosError;
        if (axiosError.isAxiosError && axiosError.response) {
          const status = axiosError.response.status;
          if (status === 404 || status === 422) {
            setErrorMessage(
              `指定されたユーザー (ID: ${userId}) は存在しません。`
            );
          } else if (status === 403) {
            setErrorMessage(
              `このユーザーを編集する権限がありません。ステータス: ${axiosError.response.status}`
            );
          } else {
            setErrorMessage(
              `ユーザー情報の取得に失敗しました。ステータス: ${axiosError.response.status}`
            );
          }
        }
      }
    };
    if (accessToken && userId) fetchUser();
  }, [accessToken, userId]);

  const handleUpdate = useCallback(async (): Promise<void> => {
    setErrorMessage("");
    try {
      if (!firstName || firstName.trim() === "") {
        setErrorMessage("名は必須項目です");
        return;
      }
      if (!lastName || lastName.trim() === "") {
        setErrorMessage("姓は必須項目です");
        return;
      }
      if (!email || email.trim() === "") {
        setErrorMessage("メールアドレスは必須項目です");
        return;
      }
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (email && !emailRegex.test(email)) {
        setErrorMessage("有効なメールアドレスを入力してください");
        return;
      }
      const payload = {
        first_name: firstName,
        last_name: lastName,
        email: email,
        role: role,
        status: status,
        customer_id: customer || null,
      };
      const res = await axios.put(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/users/${userId}`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
        }
      );
      if (res.status === 200) {
        console.log("ユーザー情報が更新されました");
        router.push(`/users/${userId}`);
      }
    } catch (error) {
      if (error instanceof AxiosError) {
        console.error("Axios エラー:", error.response?.data);
        const detail = error.response?.data?.detail || "";
        console.error("更新エラー詳細:", error.response?.data);
        setErrorMessage(detail);
      }
    }
  }, [
    firstName,
    lastName,
    email,
    role,
    status,
    customer,
    accessToken,
    userId,
    router,
    setErrorMessage,
  ]);

  const handleCancel = useCallback((): void => {
    router.push(`/users/${userId}`);
  }, [router, userId]);

  const handleSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      handleUpdate();
    },
    [handleUpdate]
  );
  return {
    firstName,
    setFirstName,
    lastName,
    setLastName,
    email,
    setEmail,
    status,
    setStatus,
    role,
    setRole,
    customer,
    setCustomer,
    errorMessage,
    setErrorMessage,
    handleSubmit,
    handleCancel,
  };
};
