export type RoomDocument = {
  role: string
  uri: string
  checksum: string
}

export type RoomRead = {
  id: string
  name: string
  room_type: 'sale' | 'develop'
  timezone: string
  founder_sub: string
  handoff_id: string
  staffing_unlocked: boolean
  created_at: string
  strategy: {
    strategy_id: string
    strategy_version: string
    offer: string
    audience: string
    hot_criteria: string
    utp?: string | null
    documents?: RoomDocument[] | null
    staffing_intent?: Record<string, unknown> | null
  }
  pending_strategy?: {
    proposal_id: string
    strategy_version: string
    offer: string
    audience: string
    hot_criteria: string
    status: 'pending'
  } | null
}

export type FunctionSlot = {
  id: string
  room_id: string
  role_key: string
  seat_index: number
  level_min?: string | null
  status: 'open' | 'filled' | 'cancelled'
  freelancer_sub?: string | null
}

export type SlotsList = {
  room_id: string
  staffing_unlocked: boolean
  slots: FunctionSlot[]
}

export type MaterializeResult = {
  room_id: string
  status: 'materialized' | 'already_materialized'
  slots: FunctionSlot[]
}

export type TaskStatus = 'todo' | 'in_progress' | 'done'

export type RoomTask = {
  id: string
  room_id: string
  title: string
  status: TaskStatus
  assignee_sub?: string | null
  created_at: string
  updated_at: string
}

export type TasksList = {
  room_id: string
  tasks: RoomTask[]
}
