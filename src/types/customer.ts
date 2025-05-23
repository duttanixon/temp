export type CustomerStatus = "ACTIVE" | "INACTIVE";

export interface Customer {
  customer_id: string;
  name: string;
  contact_email: string;
  address?: string;
  status: CustomerStatus;
  iot_thing_group_name?: string;
  iot_thing_group_arn?: string;
  created_at: string;
  updated_at?: string;
}

// Types for create/update operations
export type CustomerCreateData = {
  name: string;
  contact_email: string;
  address?: string;
};

export type CustomerUpdateData = {
  name: string;
  contact_email: string;
  address?: string;
  status: CustomerStatus;
};
