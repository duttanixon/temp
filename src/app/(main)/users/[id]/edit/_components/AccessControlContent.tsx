// import { cva } from "class-variance-authority";
// import { AccessFormField } from "@/app/(main)/users/_components/AccessFormField";
// import { FieldErrors, UseFormRegister } from "react-hook-form";
// import { UserEditFormValues } from "@/schemas/userSchemas";

// type Props = {
//   register: UseFormRegister<UserEditFormValues>;
//   errors: FieldErrors;
//   customers: { name: string; customer_id: string }[];
// };

// export const formVariants = cva("", {
//   variants: {
//     variant: {
//       label: "text-sm font-normal text-[#7F8C8D]",
//       inputName: "w-75 h-10 border border-[#BDC3C7] text-sm rounded-md",
//       input: "w-155 h-10 border border-[#BDC3C7] rounded-md",
//       userInfo: "text-lg font-bold text-[#2C3E50]",
//     },
//   },
//   defaultVariants: {
//     variant: "userInfo",
//   },
// });
// export const AccessControlContent = ({
//   register,
//   errors,
//   customers,
// }: Props) => {
//   return (
//     <>
//       <div className="flex items-center gap-x-16">
//         <h2 className={formVariants({ variant: "userInfo" })}>アクセス制御</h2>
//         <span className="text-sm font-normal text-[#7F8C8D]"></span>
//       </div>
//       <div className="flex flex-col items-center gap-2">
//         <div className="flex gap-5">
//           <AccessFormField
//             id="role"
//             label="権限"
//             type="select"
//             register={register}
//             errors={errors}
//             required
//             labelClassName={formVariants({ variant: "label" })}
//             inputClassName={formVariants({ variant: "inputName" })}
//             placeholder="選択してください"
//             options={[
//               { label: "システム管理者", value: "ADMIN" },
//               { label: "エンジニア", value: "ENGINEER" },
//               { label: "顧客", value: "CUSTOMER_ADMIN" },
//             ]}
//           />
//           <AccessFormField
//             id="customer_id"
//             label="顧客"
//             type="select"
//             register={register}
//             errors={errors}
//             labelClassName={formVariants({ variant: "label" })}
//             inputClassName={formVariants({ variant: "inputName" })}
//             placeholder="選択してください(任意)"
//             options={[
//               { label: "選択しない", value: "none" },
//               ...customers.map(
//                 (customer: { name: string; customer_id: string }) => ({
//                   label: customer.name,
//                   value: customer.customer_id,
//                 })
//               ),
//             ]}
//           />
//         </div>
//       </div>
//     </>
//   );
// };
