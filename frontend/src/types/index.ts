export interface User {
  username: string;
  role: string;
  email: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface BudgetItem {
  Description: string;
  "Qty": number;
  "$ per unit": number;
  "$ (Total)": number;
}

export interface SOAItem {
  Description: string;
  "Actual ($)": number;
  "Budgeted ($)": number;
  "Variance ($)": number;
}

export interface BudgetRequest {
  event_name: string;
  event_date: string;
  participants: number;
  volunteers: number;
  income_items: BudgetItem[];
  expense_items: BudgetItem[];
  prepared_by: string;
  designation: string;
  vetted_by: string;
}

export interface SOARequest {
  event_name: string;
  event_date: string;
  venue: string;
  activity_code: string;
  income_items: SOAItem[];
  expense_items: SOAItem[];
  prepared_by: string;
  designation_prepared: string;
  certified_by: string;
  designation_certified: string;
}

export interface ProcessedReceipt {
  merchant_name: string;
  income_items: any[];
  expenditure_items: any[];
  total_income: number;
  total_expenditure: number;
  tax_amount: number;
}

export interface ReceiptProcessingResponse {
  processed_receipts: number;
  income_items: any[];
  expenditure_items: any[];
  receipts_data: ProcessedReceipt[];
}