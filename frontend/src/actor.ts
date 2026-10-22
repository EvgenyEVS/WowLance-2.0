/** AUTH_DISABLED demo actor. Override with sessionStorage `wowlance_actor_sub`. */
export const DEMO_ACTOR_SUB = 'founder-demo-sub'

export function viewerSub(): string {
  try {
    return sessionStorage.getItem('wowlance_actor_sub') || DEMO_ACTOR_SUB
  } catch {
    return DEMO_ACTOR_SUB
  }
}
