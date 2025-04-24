import { CustomerForm } from "./_components/CustomerForm";

export default function AddCustomerPage() {
  return (
    <div className="p-8">
      <h2 className="text-[#7F8C8D] text-sm">顧客 &gt; 新規顧客追加</h2>
      <h1 className="text-[#2C3E50] text-2xl font-bold mb-6">新規顧客追加</h1>
      <CustomerForm />
    </div>
  );
}
