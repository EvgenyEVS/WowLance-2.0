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
  meeting_url?: string | null
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

export type RematerializeResult = {
  room_id: string
  status: 'rematerialized' | 'already_synced'
  slots: FunctionSlot[]
  orphaned_filled: FunctionSlot[]
}

export type RosterMember = {
  freelancer_sub: string
  display_name: string
  skills?: string[] | null
  level?: string | null
  source?: 'stub' | 'talent'
}

export type RosterList = {
  members: RosterMember[]
}

export type RosterUpsertResult = {
  freelancer_sub: string
  status: 'upserted' | 'already_exists'
}

export type SlotAssignResult = {
  slot: FunctionSlot
  status: 'assigned' | 'already_assigned'
}

export type SlotUnassignResult = {
  slot: FunctionSlot
  status: 'unassigned'
}

export type SlotReassignResult = {
  slot: FunctionSlot
  status: 'reassigned' | 'already_assigned'
}

export type TaskStatus = 'todo' | 'in_progress' | 'submitted' | 'done'

export type RoomTask = {
  id: string
  room_id: string
  title: string
  status: TaskStatus
  assignee_sub?: string | null
  proof_uri?: string | null
  proof_note?: string | null
  reviewed_by_sub?: string | null
  review_note?: string | null
  created_at: string
  updated_at: string
}

export type TasksList = {
  room_id: string
  tasks: RoomTask[]
}

export type LeadStatus = 'open' | 'hot' | 'handed_to_crm'

export type RoomLead = {
  id: string
  room_id: string
  title: string
  contact_name?: string | null
  contact_email?: string | null
  notes?: string | null
  status: LeadStatus
  crm_ref?: string | null
  deal_status?: string | null
  deal_amount?: string | null
  deal_currency?: string | null
  deal_updated_at?: string | null
  created_at: string
  updated_at: string
}

export type LeadsList = {
  room_id: string
  leads: RoomLead[]
}

export type LeadHandoffResult = {
  lead: RoomLead
  crm_ref: string
  status: 'handed' | 'already_handed'
}

export type RoomHealth = {
  room_id: string
  captured_at: string
  room: {
    room_type: 'sale' | 'develop'
    name: string
    staffing_unlocked: boolean
    strategy_id?: string | null
    strategy_version?: string | null
  }
  slots: { total: number; open: number; filled: number; cancelled: number }
  tasks: { todo: number; in_progress: number; submitted: number; done: number }
  leads: { total: number; hot: number; handed_to_crm: number }
  earnings: { total_amount: string; currency: string; entries_count: number }
}

export type RoomHealthEarnings = {
  total_amount: string
  currency: string
  entries_count: number
}

export type RoomHealthPublishResult = {
  outbox_id: string
  event_type: 'RoomHealthSnapshot'
  status: 'published'
  snapshot: RoomHealth
}

export type MeetEnsureResult = {
  meeting_url: string
  status: 'created' | 'already_exists'
}

export type EarningsEntry = {
  id: string
  room_id: string
  task_id: string
  freelancer_sub: string
  amount: string
  currency: string
  source: string
  created_at: string
}

export type EarningsList = {
  room_id: string
  total_amount: string
  currency: string
  entries: EarningsEntry[]
}

export type TerminateMemberResult = {
  status: 'terminated'
  freelancer_sub: string
  slot_ids: string[]
}

export type RoomMessage = {
  id: string
  room_id: string
  author_sub: string
  body: string
  created_at: string
}

export type MessagesList = {
  room_id: string
  messages: RoomMessage[]
}
