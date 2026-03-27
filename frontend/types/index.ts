export type MockDataRow = {
  employee_id: string
  name: string
  department: string
  position: string
  manager_name: string
  remaining_vacation_days: number | null
  pay_grade: string | null
  gross_annual: number | null
  currency: string
}

export type MockDataOverview = {
  employee_count: number
  departments: string[]
  rows: MockDataRow[]
}
