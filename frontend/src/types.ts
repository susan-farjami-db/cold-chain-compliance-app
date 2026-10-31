export interface ComplianceRow {
  row_id: string;
  unit_number: string;
  trailer_type: string;
  owner_name: string;
  last_update_date: string;
  last_change_description: string;
  updated_by: string;
  pending_action_items: string;
  tval_status: string;
  recert_appt_date: string;
}

export interface BootstrapData {
  rows: ComplianceRow[];
  units: string[];
  tval_statuses: string[];
  user: string;
}

export const TVAL_COMPLIANT = 'Compliant for T-Val';
