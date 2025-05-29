"use client";
import DeviceTable from "@/app/(main)/devices/_components/DeviceTable";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { customerService } from "@/services/customerService";
import { customerSolutionService } from "@/services/customerSolutionService";
import { deviceService } from "@/services/deviceService";
import { userService } from "@/services/userService";
import { Customer } from "@/types/customer";
import { CustomerAssignment } from "@/types/customerSolution";
import { Device } from "@/types/device";
import { User } from "@/types/user";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import UserPagination from "../../users/_components/Pagination";
import UserTable from "../../users/_components/UserTable";
import CustomerSolutionTable from "./_components/CustomerSolutionTable";

export default function CustomerOverviewPage() {
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [devices, setDevices] = useState<Device[]>([]);
  const [totalDevices, setTotalDevices] = useState(0);
  const [activeDevices, setActiveDevices] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [userPage, setUserPage] = useState(0);
  const [totalUsers, setTotalUsers] = useState(0);
  const [activeUsers, setActiveUsers] = useState(0);
  const [solutions, setSolutions] = useState<CustomerAssignment[]>([]);

  const params = useParams();
  const customerId = params?.id as string;
  useEffect(() => {
    const fetchCustomer = async () => {
      try {
        setLoading(true);
        const customerData = await customerService.getCustomer(customerId);
        if (!customerData) {
          return <div>customerDataがありません</div>;
        }
        setCustomer(customerData);
      } catch (error) {
        console.error("Failed to fetch customer:", error);
        return <div>顧客情報の取得に失敗しました</div>;
      } finally {
        setLoading(false);
      }
    };

    if (customerId) {
      fetchCustomer();
    }
  }, [customerId]);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setLoading(true);
        const devicesData = await deviceService.getDevices(customerId);
        setDevices(devicesData);
        const total = devicesData.length;
        setTotalDevices(total);
        const active = devicesData.filter(
          (device) => device.status === "ACTIVE"
        ).length;
        setActiveDevices(active);
      } catch (error) {
        console.error("Failed to fetch devices:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDevices();
  }, [customerId]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const usersData = await userService.getUsers(customerId);
        setUsers(usersData);
        const total = usersData.length;
        setTotalUsers(total);
        const active = usersData.filter(
          (user) => user.status === "ACTIVE"
        ).length;
        setActiveUsers(active);
      } catch (error) {
        console.error("Failed to fetch customer:", error);
      } finally {
        setUserPage(0);
        setLoading(false);
      }
    };

    fetchUsers();
  }, [customerId]);

  useEffect(() => {
    const fetchSolutions = async () => {
      try {
        setLoading(true);
        const solutionsData =
          await customerSolutionService.getCustomerAssignments({ customerId });
        const solutions = solutionsData.filter(
          (solution) => solution.customer_id === customerId
        );
        setSolutions(solutions);
      } catch (error) {
        console.error("Failed to fetch customer:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSolutions();
  }, [customerId]);

  // ローディング中の表示
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">読み込み中...</div>
      </div>
    );
  }
  if (!customer) {
    return <div>customerがありません</div>;
  }
  return (
    <div className="flex flex-col gap-4">
      {/* ヘッダー部分 */}
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-4">
          <Breadcrumb className="text-sm text-[#7F8C8D]">
            <BreadcrumbList>
              <BreadcrumbItem className=" hover:underline">
                <BreadcrumbLink href="/customers">顧客</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="text-[#7F8C8D]" />
              <BreadcrumbItem>{customer?.name}</BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="text-2xl font-bold text-gray-900">{customer?.name}</h1>
        </div>
        <Link href={`/customers/${customerId}/edit`}>
          <Button className="bg-green-600 hover:bg-green-700 text-white font-semibold px-12 py-2 rounded cursor-pointer">
            編集
          </Button>
        </Link>
      </div>

      {/* タブセクション */}
      <Tabs defaultValue="overview" className="w-full flex flex-col gap-4">
        <TabsList className="grid w-fit grid-cols-4 h-full bg-white border border-gray-200 rounded-lg p-0">
          <TabsTrigger
            value="overview"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-3"
          >
            概要
          </TabsTrigger>
          <TabsTrigger
            value="device"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-3"
          >
            デバイス
          </TabsTrigger>
          <TabsTrigger
            value="user"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-3"
          >
            ユーザー
          </TabsTrigger>
          <TabsTrigger
            value="solution"
            className="min-w-[115px] data-[state=active]:bg-[#3498DB] data-[state=active]:text-white data-[state=inactive]:text-gray-600 hover:cursor-pointer py-3"
          >
            ソリューション
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="flex gap-4 max-w-2xl">
            <Card className="flex-1 bg-white shadow-sm text-gray-600">
              <CardHeader className="pb-2">
                <CardTitle className="font-medium">
                  アクティブ状態のデバイス
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                {totalDevices ? (
                  <div className="flex items-baseline text-3xl font-bold text-gray-900">
                    <span>{activeDevices}</span>
                    <span>/</span>
                    <span>{totalDevices}</span>
                  </div>
                ) : (
                  <span className="text-sm">デバイスが登録されていません</span>
                )}
              </CardContent>
            </Card>

            <Card className="flex-1 bg-white shadow-sm text-gray-600">
              <CardHeader className="pb-2">
                <CardTitle className="font-medium text-gray-600">
                  アクティブ状態のユーザー
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                {totalUsers ? (
                  <div className="flex items-baseline text-3xl font-bold text-green-600">
                    <span>{activeUsers}</span>
                    <span>/</span>
                    <span>{totalUsers}</span>
                  </div>
                ) : (
                  <span className="text-sm">ユーザーが登録されていません</span>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="device">
          <DeviceTable initialDevices={devices} />
        </TabsContent>

        <TabsContent value="user">
          <UserTable
            users={users}
            page={userPage}
            setPage={setUserPage}
            itemsPerPage={10}
            userRole="ADMIN"
          />

          <div>
            <UserPagination
              page={userPage}
              setPage={setUserPage}
              totalItems={totalUsers}
              itemsPerPage={10}
            />
          </div>
        </TabsContent>

        <TabsContent value="solution">
          <CustomerSolutionTable initialSolutions={solutions} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
