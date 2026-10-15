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
}
