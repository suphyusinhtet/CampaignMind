'use client'

import type {
  AgentEvent,
  AgentListItem,
  AnalysisMetadata,
  Conversation,
  ConversationState,
  ConversationStateUpdatePayload,
  CreateConversationPayload,
  Message,
  SendMessagePayload,
  UpdateConversationPayload,
} from '@/types'
import { createClient } from '@/lib/supabase/client'
import { isGuestModeEnabled, isSupabaseConfigured } from '@/lib/supabase/config'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const GUEST_STORAGE_KEY = 'campaignmind.guest.conversations.v1'
const GUEST_RUNTIME_KEY = 'campaignmind.guest.runtime.v1'
const GUEST_RUNTIME_DATA_KEY = 'campaignmind.guest.runtime_data.v1'
const GUEST_SESSION_KEY = 'campaignmind.guest.session.id'
const GUEST_SCHEMA_KEY = 'campaignmind.guest.schema.version'
const GUEST_CLEANUP_KEY = 'campaignmind.guest.cleanup.last'
const GUEST_SCHEMA_VERSION = 2
const GUEST_DB_NAME = 'campaignmind_guest_db'
const GUEST_DB_VERSION = 1
const GUEST_CONVERSATIONS_STORE = 'conversations'
const GUEST_RUNTIME_DATA_STORE = 'runtime_data'
const GUEST_TTL_MS = 1000 * 60 * 60 * 24 * 30 // 30 days
const GUEST_CLEANUP_INTERVAL_MS = 1000 * 60 * 60 * 6 // 6 hours
const GUEST_USER_ID = 'guest-user'
const MAX_CONVERSATION_TITLE_CHARS = 60
const MAX_CONVERSATION_TITLE_WORDS = 10
const CONTINUE_WORDS = new Set([
  'continue',
  'next',
  'go',
  'run',
  'proceed',
  'interactive',
  'interactively',
])
const METADATA_CONFIRM_WORDS = new Set([
  'confirm',
  'confirmed',
  'yes',
  'y',
  'ok',
  'okay',
  'continue',
  'proceed',
  'run',
])
const REQUIRED_GUEST_METADATA_FIELDS = [
  'brand_name',
  'sector',
  'target_audience',
  'objectives_kpis',
  'competitors',
  'budget',
  'timing',
  'geography',
] as const

type RequiredGuestMetadataField = (typeof REQUIRED_GUEST_METADATA_FIELDS)[number]

type GuestStep =
  | 'idle'
  | 'awaiting_user_metadata'
  | 'awaiting_user_metadata_confirmation'
  | 'awaiting_user_mode_selection'
  | 'running_pipeline'
  | 'awaiting_user_continue_trend'
  | 'awaiting_user_continue_case'
  | 'awaiting_user_continue_landscape'
  | 'awaiting_user_continue_insight'
  | 'awaiting_user_continue_creator'
  | 'awaiting_user_creator_option'
  | 'completed'

interface GuestConversationRuntime {
  mode: 'interactive' | 'autonomous'
  current_step: GuestStep
  pipeline_status: string
  pending_prompt: string | null
  required_metadata?: Record<string, string>
  updated_at: string
}

type GuestRuntimeMap = Record<string, GuestConversationRuntime>
type GuestRuntimeDataMap = Record<
  string,
  {
    cached_analysis?: AnalysisMetadata & { final_insights?: string }
    events: AgentEvent[]
    updated_at: string
  }
>

interface GuestRuntimeDataRecord {
  conversation_id: string
  cached_analysis?: AnalysisMetadata & { final_insights?: string }
  events: AgentEvent[]
  updated_at: string
}

type LegacyGuestRuntime = GuestConversationRuntime & {
  cached_analysis?: AnalysisMetadata & { final_insights?: string }
  events?: AgentEvent[]
}

let guestStorageReadyPromise: Promise<void> | null = null

async function getAccessToken(): Promise<string | null> {
  if (!isSupabaseConfigured) return null

  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()

  return session?.access_token ?? null
}

function getGuestSessionId(): string | null {
  if (typeof window === 'undefined') return null
  let current = window.localStorage.getItem(GUEST_SESSION_KEY)
  if (current && current.trim().length > 0) return current
  current = `guest-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
  window.localStorage.setItem(GUEST_SESSION_KEY, current)
  return current
}

function guestNow() {
  return new Date().toISOString()
}

function guestId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function readGuestConversationsFromLocal(): Conversation[] {
  if (typeof window === 'undefined') return []
  const raw = window.localStorage.getItem(GUEST_STORAGE_KEY)
  if (!raw) return []

  try {
    const parsed = JSON.parse(raw) as Conversation[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeGuestConversationsToLocal(conversations: Conversation[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(conversations))
}

function readGuestRuntimeDataMapLocal(): GuestRuntimeDataMap {
  if (typeof window === 'undefined') return {}
  const raw = window.localStorage.getItem(GUEST_RUNTIME_DATA_KEY)
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw) as GuestRuntimeDataMap
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeGuestRuntimeDataMapLocal(runtimeData: GuestRuntimeDataMap) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(GUEST_RUNTIME_DATA_KEY, JSON.stringify(runtimeData))
}

function normalizeConversationTitle(title: string) {
  let normalized = title.trim().replace(/\s+/g, ' ')
  if (!normalized) throw new Error('Conversation title cannot be empty.')

  const words = normalized.split(' ')
  if (words.length > MAX_CONVERSATION_TITLE_WORDS) {
    normalized = words.slice(0, MAX_CONVERSATION_TITLE_WORDS).join(' ')
  }
  if (normalized.length > MAX_CONVERSATION_TITLE_CHARS) {
    normalized = normalized.slice(0, MAX_CONVERSATION_TITLE_CHARS).trimEnd()
  }
  if (!normalized) throw new Error('Conversation title cannot be empty.')
  return normalized
}

function readGuestRuntimeMap(): GuestRuntimeMap {
  if (typeof window === 'undefined') return {}
  const raw = window.localStorage.getItem(GUEST_RUNTIME_KEY)
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw) as GuestRuntimeMap
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeGuestRuntimeMap(runtime: GuestRuntimeMap) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(GUEST_RUNTIME_KEY, JSON.stringify(runtime))
}

function defaultGuestRuntime(): GuestConversationRuntime {
  return {
    mode: 'interactive',
    current_step: 'idle',
    pipeline_status: 'idle',
    pending_prompt: null,
    required_metadata: {},
    updated_at: guestNow(),
  }
}

function defaultGuestRuntimeData(conversationId: string): GuestRuntimeDataRecord {
  return {
    conversation_id: conversationId,
    cached_analysis: undefined,
    events: [],
    updated_at: guestNow(),
  }
}

function getGuestRuntime(conversationId: string): GuestConversationRuntime {
  const all = readGuestRuntimeMap()
  return all[conversationId] ?? defaultGuestRuntime()
}

function setGuestRuntime(conversationId: string, runtime: GuestConversationRuntime) {
  const all = readGuestRuntimeMap()
  all[conversationId] = {
    ...runtime,
    updated_at: guestNow(),
  }
  writeGuestRuntimeMap(all)
}

function requestToPromise<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('IndexedDB request failed'))
  })
}

function transactionDone(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error ?? new Error('IndexedDB transaction failed'))
    tx.onabort = () => reject(tx.error ?? new Error('IndexedDB transaction aborted'))
  })
}

function hasIndexedDb() {
  return typeof window !== 'undefined' && typeof window.indexedDB !== 'undefined'
}

async function openGuestDb(): Promise<IDBDatabase> {
  if (!hasIndexedDb()) throw new Error('IndexedDB is not available')
  const request = window.indexedDB.open(GUEST_DB_NAME, GUEST_DB_VERSION)

  request.onupgradeneeded = () => {
    const db = request.result
    if (!db.objectStoreNames.contains(GUEST_CONVERSATIONS_STORE)) {
      db.createObjectStore(GUEST_CONVERSATIONS_STORE, { keyPath: 'id' })
    }
    if (!db.objectStoreNames.contains(GUEST_RUNTIME_DATA_STORE)) {
      db.createObjectStore(GUEST_RUNTIME_DATA_STORE, { keyPath: 'conversation_id' })
    }
  }

  return requestToPromise(request)
}

async function listDbConversations(db: IDBDatabase): Promise<Conversation[]> {
  const tx = db.transaction(GUEST_CONVERSATIONS_STORE, 'readonly')
  const store = tx.objectStore(GUEST_CONVERSATIONS_STORE)
  const rows = await requestToPromise<Conversation[]>(store.getAll())
  await transactionDone(tx)
  return Array.isArray(rows) ? rows : []
}

async function putDbConversation(db: IDBDatabase, conversation: Conversation): Promise<void> {
  const tx = db.transaction(GUEST_CONVERSATIONS_STORE, 'readwrite')
  tx.objectStore(GUEST_CONVERSATIONS_STORE).put(conversation)
  await transactionDone(tx)
}

async function deleteDbConversation(db: IDBDatabase, conversationId: string): Promise<void> {
  const tx = db.transaction(GUEST_CONVERSATIONS_STORE, 'readwrite')
  tx.objectStore(GUEST_CONVERSATIONS_STORE).delete(conversationId)
  await transactionDone(tx)
}

async function getDbConversation(
  db: IDBDatabase,
  conversationId: string,
): Promise<Conversation | null> {
  const tx = db.transaction(GUEST_CONVERSATIONS_STORE, 'readonly')
  const conversation = await requestToPromise<Conversation | undefined>(
    tx.objectStore(GUEST_CONVERSATIONS_STORE).get(conversationId),
  )
  await transactionDone(tx)
  return conversation ?? null
}

async function listDbRuntimeData(db: IDBDatabase): Promise<GuestRuntimeDataRecord[]> {
  const tx = db.transaction(GUEST_RUNTIME_DATA_STORE, 'readonly')
  const store = tx.objectStore(GUEST_RUNTIME_DATA_STORE)
  const rows = await requestToPromise<GuestRuntimeDataRecord[]>(store.getAll())
  await transactionDone(tx)
  return Array.isArray(rows) ? rows : []
}

async function getDbRuntimeData(
  db: IDBDatabase,
  conversationId: string,
): Promise<GuestRuntimeDataRecord | null> {
  const tx = db.transaction(GUEST_RUNTIME_DATA_STORE, 'readonly')
  const record = await requestToPromise<GuestRuntimeDataRecord | undefined>(
    tx.objectStore(GUEST_RUNTIME_DATA_STORE).get(conversationId),
  )
  await transactionDone(tx)
  return record ?? null
}

async function putDbRuntimeData(
  db: IDBDatabase,
  record: GuestRuntimeDataRecord,
): Promise<void> {
  const tx = db.transaction(GUEST_RUNTIME_DATA_STORE, 'readwrite')
  tx.objectStore(GUEST_RUNTIME_DATA_STORE).put(record)
  await transactionDone(tx)
}

async function deleteDbRuntimeData(db: IDBDatabase, conversationId: string): Promise<void> {
  const tx = db.transaction(GUEST_RUNTIME_DATA_STORE, 'readwrite')
  tx.objectStore(GUEST_RUNTIME_DATA_STORE).delete(conversationId)
  await transactionDone(tx)
}

function safeTimestampMs(raw: string | undefined | null): number | null {
  if (!raw) return null
  const ms = Date.parse(raw)
  return Number.isFinite(ms) ? ms : null
}

function isExpiredByTtl(raw: string | undefined | null, cutoffMs: number): boolean {
  const timestamp = safeTimestampMs(raw)
  if (timestamp === null) return false
  return timestamp < cutoffMs
}

async function migrateLegacyGuestStorage(db: IDBDatabase): Promise<void> {
  const localConversations = readGuestConversationsFromLocal()
  if (localConversations.length > 0) {
    const existingDb = await listDbConversations(db)
    if (existingDb.length === 0) {
      for (const conversation of localConversations) {
        await putDbConversation(db, conversation)
      }
    }
  }

  const runtimeMap = readGuestRuntimeMap() as Record<string, LegacyGuestRuntime>
  const nextRuntimeMap: GuestRuntimeMap = {}
  for (const [conversationId, runtime] of Object.entries(runtimeMap)) {
    const lightweight: GuestConversationRuntime = {
      mode: runtime?.mode === 'autonomous' ? 'autonomous' : 'interactive',
      current_step: (runtime?.current_step as GuestStep) ?? 'idle',
      pipeline_status: runtime?.pipeline_status ?? 'idle',
      pending_prompt: runtime?.pending_prompt ?? null,
      required_metadata:
        runtime?.required_metadata && typeof runtime.required_metadata === 'object'
          ? runtime.required_metadata
          : {},
      updated_at: runtime?.updated_at ?? guestNow(),
    }
    nextRuntimeMap[conversationId] = lightweight

    const hasHeavy =
      runtime?.cached_analysis ||
      (Array.isArray(runtime?.events) && runtime.events.length > 0)
    if (hasHeavy) {
      await putDbRuntimeData(db, {
        conversation_id: conversationId,
        cached_analysis: runtime.cached_analysis,
        events: Array.isArray(runtime.events) ? runtime.events : [],
        updated_at: runtime?.updated_at ?? guestNow(),
      })
    }
  }
  writeGuestRuntimeMap(nextRuntimeMap)
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(GUEST_STORAGE_KEY)
  }
}

async function runGuestTtlCleanup(db: IDBDatabase): Promise<void> {
  if (typeof window === 'undefined') return
  const nowMs = Date.now()
  const lastCleanupMs = Number(window.localStorage.getItem(GUEST_CLEANUP_KEY) ?? '0')
  if (Number.isFinite(lastCleanupMs) && lastCleanupMs > 0 && nowMs - lastCleanupMs < GUEST_CLEANUP_INTERVAL_MS) {
    return
  }

  const cutoffMs = nowMs - GUEST_TTL_MS
  const conversations = await listDbConversations(db)
  const activeConversationIds = new Set<string>()
  for (const conversation of conversations) {
    const marker = conversation.updated_at || conversation.created_at
    if (isExpiredByTtl(marker, cutoffMs)) {
      await deleteDbConversation(db, conversation.id)
      await deleteDbRuntimeData(db, conversation.id)
      continue
    }
    activeConversationIds.add(conversation.id)
  }

  const runtimeMap = readGuestRuntimeMap()
  let runtimeChanged = false
  for (const [conversationId, runtime] of Object.entries(runtimeMap)) {
    const missingConversation = !activeConversationIds.has(conversationId)
    if (missingConversation || isExpiredByTtl(runtime.updated_at, cutoffMs)) {
      delete runtimeMap[conversationId]
      runtimeChanged = true
    }
  }
  if (runtimeChanged) {
    writeGuestRuntimeMap(runtimeMap)
  }

  const runtimeDataRows = await listDbRuntimeData(db)
  for (const row of runtimeDataRows) {
    const missingConversation = !activeConversationIds.has(row.conversation_id)
    if (missingConversation || isExpiredByTtl(row.updated_at, cutoffMs)) {
      await deleteDbRuntimeData(db, row.conversation_id)
    }
  }

  window.localStorage.setItem(GUEST_CLEANUP_KEY, String(nowMs))
}

function runGuestTtlCleanupLocalStorage(): void {
  if (typeof window === 'undefined') return
  const nowMs = Date.now()
  const lastCleanupMs = Number(window.localStorage.getItem(GUEST_CLEANUP_KEY) ?? '0')
  if (Number.isFinite(lastCleanupMs) && lastCleanupMs > 0 && nowMs - lastCleanupMs < GUEST_CLEANUP_INTERVAL_MS) {
    return
  }
  const cutoffMs = nowMs - GUEST_TTL_MS

  const conversations = readGuestConversationsFromLocal()
  const filteredConversations = conversations.filter((conversation) => {
    const marker = conversation.updated_at || conversation.created_at
    return !isExpiredByTtl(marker, cutoffMs)
  })
  writeGuestConversationsToLocal(filteredConversations)
  const activeConversationIds = new Set(filteredConversations.map((c) => c.id))

  const runtimeMap = readGuestRuntimeMap()
  let runtimeChanged = false
  for (const [conversationId, runtime] of Object.entries(runtimeMap)) {
    const missingConversation = !activeConversationIds.has(conversationId)
    if (missingConversation || isExpiredByTtl(runtime.updated_at, cutoffMs)) {
      delete runtimeMap[conversationId]
      runtimeChanged = true
    }
  }
  if (runtimeChanged) {
    writeGuestRuntimeMap(runtimeMap)
  }

  const runtimeDataMap = readGuestRuntimeDataMapLocal()
  let runtimeDataChanged = false
  for (const [conversationId, runtimeData] of Object.entries(runtimeDataMap)) {
    const missingConversation = !activeConversationIds.has(conversationId)
    if (missingConversation || isExpiredByTtl(runtimeData.updated_at, cutoffMs)) {
      delete runtimeDataMap[conversationId]
      runtimeDataChanged = true
    }
  }
  if (runtimeDataChanged) {
    writeGuestRuntimeDataMapLocal(runtimeDataMap)
  }

  window.localStorage.setItem(GUEST_CLEANUP_KEY, String(nowMs))
}

async function ensureGuestStorageReady(): Promise<void> {
  if (typeof window === 'undefined') return
  if (!hasIndexedDb()) {
    runGuestTtlCleanupLocalStorage()
    return
  }
  if (guestStorageReadyPromise) {
    await guestStorageReadyPromise
    return
  }

  guestStorageReadyPromise = (async () => {
    const db = await openGuestDb()
    try {
      const schemaVersion = Number(window.localStorage.getItem(GUEST_SCHEMA_KEY) ?? '1')
      if (!Number.isFinite(schemaVersion) || schemaVersion < GUEST_SCHEMA_VERSION) {
        await migrateLegacyGuestStorage(db)
        window.localStorage.setItem(GUEST_SCHEMA_KEY, String(GUEST_SCHEMA_VERSION))
      }
      await runGuestTtlCleanup(db)
    } finally {
      db.close()
    }
  })().catch(() => {
    // Keep guest mode functional even if IndexedDB initialization fails.
  })

  await guestStorageReadyPromise
}

async function readGuestConversations(): Promise<Conversation[]> {
  if (typeof window === 'undefined') return []
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    return readGuestConversationsFromLocal()
  }
  try {
    const db = await openGuestDb()
    try {
      return await listDbConversations(db)
    } finally {
      db.close()
    }
  } catch {
    return readGuestConversationsFromLocal()
  }
}

async function getGuestConversationById(conversationId: string): Promise<Conversation | null> {
  if (typeof window === 'undefined') return null
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    return readGuestConversationsFromLocal().find((c) => c.id === conversationId) ?? null
  }
  try {
    const db = await openGuestDb()
    try {
      return await getDbConversation(db, conversationId)
    } finally {
      db.close()
    }
  } catch {
    return readGuestConversationsFromLocal().find((c) => c.id === conversationId) ?? null
  }
}

async function saveGuestConversation(conversation: Conversation): Promise<void> {
  if (typeof window === 'undefined') return
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    const conversations = readGuestConversationsFromLocal()
    const index = conversations.findIndex((c) => c.id === conversation.id)
    if (index >= 0) conversations[index] = conversation
    else conversations.unshift(conversation)
    writeGuestConversationsToLocal(conversations)
    return
  }
  try {
    const db = await openGuestDb()
    try {
      await putDbConversation(db, conversation)
    } finally {
      db.close()
    }
  } catch {
    const conversations = readGuestConversationsFromLocal()
    const index = conversations.findIndex((c) => c.id === conversation.id)
    if (index >= 0) conversations[index] = conversation
    else conversations.unshift(conversation)
    writeGuestConversationsToLocal(conversations)
  }
}

async function deleteGuestConversationRecord(conversationId: string): Promise<void> {
  if (typeof window === 'undefined') return
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    const updated = readGuestConversationsFromLocal().filter((c) => c.id !== conversationId)
    writeGuestConversationsToLocal(updated)
    return
  }
  try {
    const db = await openGuestDb()
    try {
      await deleteDbConversation(db, conversationId)
      await deleteDbRuntimeData(db, conversationId)
    } finally {
      db.close()
    }
  } catch {
    const updated = readGuestConversationsFromLocal().filter((c) => c.id !== conversationId)
    writeGuestConversationsToLocal(updated)
  }
}

async function getGuestRuntimeData(conversationId: string): Promise<GuestRuntimeDataRecord> {
  if (typeof window === 'undefined') return defaultGuestRuntimeData(conversationId)
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    const map = readGuestRuntimeDataMapLocal()
    const record = map[conversationId]
    if (!record) return defaultGuestRuntimeData(conversationId)
    return {
      conversation_id: conversationId,
      cached_analysis: record.cached_analysis,
      events: Array.isArray(record.events) ? record.events : [],
      updated_at: record.updated_at ?? guestNow(),
    }
  }

  try {
    const db = await openGuestDb()
    try {
      const fromDb = await getDbRuntimeData(db, conversationId)
      return fromDb ?? defaultGuestRuntimeData(conversationId)
    } finally {
      db.close()
    }
  } catch {
    const map = readGuestRuntimeDataMapLocal()
    const record = map[conversationId]
    if (!record) return defaultGuestRuntimeData(conversationId)
    return {
      conversation_id: conversationId,
      cached_analysis: record.cached_analysis,
      events: Array.isArray(record.events) ? record.events : [],
      updated_at: record.updated_at ?? guestNow(),
    }
  }
}

async function setGuestRuntimeData(
  conversationId: string,
  runtimeData: GuestRuntimeDataRecord,
): Promise<void> {
  const payload: GuestRuntimeDataRecord = {
    conversation_id: conversationId,
    cached_analysis: runtimeData.cached_analysis,
    events: Array.isArray(runtimeData.events) ? runtimeData.events : [],
    updated_at: guestNow(),
  }

  if (typeof window === 'undefined') return
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    const map = readGuestRuntimeDataMapLocal()
    map[conversationId] = payload
    writeGuestRuntimeDataMapLocal(map)
    return
  }
  try {
    const db = await openGuestDb()
    try {
      await putDbRuntimeData(db, payload)
    } finally {
      db.close()
    }
  } catch {
    const map = readGuestRuntimeDataMapLocal()
    map[conversationId] = payload
    writeGuestRuntimeDataMapLocal(map)
  }
}

async function deleteGuestRuntimeData(conversationId: string): Promise<void> {
  if (typeof window === 'undefined') return
  await ensureGuestStorageReady()

  if (!hasIndexedDb()) {
    const map = readGuestRuntimeDataMapLocal()
    delete map[conversationId]
    writeGuestRuntimeDataMapLocal(map)
    return
  }
  try {
    const db = await openGuestDb()
    try {
      await deleteDbRuntimeData(db, conversationId)
    } finally {
      db.close()
    }
  } catch {
    const map = readGuestRuntimeDataMapLocal()
    delete map[conversationId]
    writeGuestRuntimeDataMapLocal(map)
  }
}

function appendGuestEvent(
  runtimeData: GuestRuntimeDataRecord,
  conversationId: string,
  event: Omit<AgentEvent, 'conversation_id' | 'created_at'>,
) {
  runtimeData.events.push({
    ...event,
    conversation_id: conversationId,
    created_at: guestNow(),
  })
}

function parseJsonPayload(raw?: string) {
  if (!raw) return null
  const match = raw.match(/```json\s*([\s\S]*?)\s*```/)
  const text = match ? match[1] : raw
  try {
    const parsed = JSON.parse(text)
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch {
    return null
  }
}

function extractGuestMetadataFromText(text: string): Partial<Record<RequiredGuestMetadataField, string>> {
  const result: Partial<Record<RequiredGuestMetadataField, string>> = {}
  const lines = text.split('\n').map((line) => line.trim()).filter(Boolean)
  const joined = lines.join('\n')

  const lineValue = (aliases: string[]) => {
    for (const line of lines) {
      const lower = line.toLowerCase()
      for (const alias of aliases) {
        if (!lower.startsWith(`${alias.toLowerCase()}:`)) continue
        const value = line.slice(line.indexOf(':') + 1).trim()
        if (value) return value
      }
    }
    return ''
  }

  const blockValue = (heading: string) => {
    const headingRegex = new RegExp(`(^|\\n)${heading}\\s*\\n([\\s\\S]*?)(?=\\n[A-Z][A-Z &/_-]{2,}|$)`, 'i')
    const match = joined.match(headingRegex)
    if (!match?.[2]) return ''
    const value = match[2].replace(/\s+/g, ' ').trim()
    return value
  }

  const brand = lineValue(['brand name', 'target brand', 'brand', 'company name', 'company'])
  const sector = lineValue(['sector', 'industry'])
  const audience = lineValue(['target audience', 'audience'])
  const objectives = lineValue(['objectives/kpis', 'objectives', 'kpis', 'objectives & kpis'])
  const competitors = lineValue(['competitors', 'competitor'])
  const budget = lineValue(['budget'])
  const timing = lineValue(['timing', 'timeline'])
  const geography = lineValue(['geography', 'market', 'country', 'region'])

  if (brand) result.brand_name = brand
  if (sector) result.sector = sector
  if (audience) result.target_audience = audience
  if (objectives) result.objectives_kpis = objectives
  if (competitors) result.competitors = competitors
  if (budget) result.budget = budget
  if (timing) result.timing = timing
  if (geography) result.geography = geography

  if (!result.brand_name) {
    const briefMatch = joined.match(/brief\s*[-:]\s*([^\n]+)/i)
    if (briefMatch?.[1]) result.brand_name = briefMatch[1].trim()
  }
  if (!result.sector) {
    const sectorBlock = blockValue('PRODUCT OR\\s*SERVICE')
    if (sectorBlock) {
      if (sectorBlock.toLowerCase().includes('insurance')) result.sector = 'Insurance'
      else if (sectorBlock.toLowerCase().includes('supermarket')) result.sector = 'Supermarket'
    }
  }
  if (!result.target_audience) {
    const targetBlock = blockValue('TARGET\\s*AUDIENCE')
    if (targetBlock) result.target_audience = targetBlock
  }
  if (!result.objectives_kpis) {
    const objectiveBlock = blockValue('OBJECTIVES?\\s*/\\s*KPIS?')
    if (objectiveBlock) result.objectives_kpis = objectiveBlock
  }
  if (!result.competitors) {
    const compBlock = blockValue('COMPETITORS?')
    if (compBlock) result.competitors = compBlock
  }
  if (!result.budget) {
    const budgetBlock = blockValue('BUDGET')
    if (budgetBlock) result.budget = budgetBlock
  }
  if (!result.timing) {
    const timingBlock = blockValue('TIMING')
    if (timingBlock) result.timing = timingBlock
  }
  if (!result.geography) {
    const geoBlock = blockValue('GEOGRAPHY')
    if (geoBlock) result.geography = geoBlock
  }

  return result
}

function mergeGuestMetadata(
  current: Record<string, string> | undefined,
  incomingText: string,
): Record<string, string> {
  const next = { ...(current ?? {}) }
  const extracted = extractGuestMetadataFromText(incomingText)
  for (const [key, value] of Object.entries(extracted)) {
    if (value && value.trim()) next[key] = value.trim()
  }
  return next
}

function missingGuestMetadata(metadata: Record<string, string> | undefined): RequiredGuestMetadataField[] {
  return REQUIRED_GUEST_METADATA_FIELDS.filter((field) => {
    const value = metadata?.[field]
    return !value || !value.trim()
  })
}

function formatGuestMissingMetadataPrompt(missing: RequiredGuestMetadataField[]) {
  const labels: Record<RequiredGuestMetadataField, string> = {
    brand_name: 'Brand Name',
    sector: 'Sector',
    target_audience: 'Target Audience',
    objectives_kpis: 'Objectives/KPIs',
    competitors: 'Competitors',
    budget: 'Budget',
    timing: 'Timing',
    geography: 'Geography',
  }
  const lines = [
    '## Required Metadata Before Specialist Agents',
    '',
    'Please provide the missing fields:',
    ...missing.map((field) => `- ${labels[field]}`),
    '',
    'Reply in this format:',
    'Brand Name: ...',
    'Sector: ...',
    'Target Audience: ...',
    'Objectives/KPIs: ...',
    'Competitors: ...',
    'Budget: ...',
    'Timing: ...',
    'Geography: ...',
  ]
  return lines.join('\n')
}

function formatGuestMetadataConfirmation(metadata: Record<string, string>) {
  return [
    '## Extracted Metadata',
    '',
    `- Brand Name: ${metadata.brand_name || '(missing)'}`,
    `- Sector: ${metadata.sector || '(missing)'}`,
    `- Target Audience: ${metadata.target_audience || '(missing)'}`,
    `- Objectives/KPIs: ${metadata.objectives_kpis || '(missing)'}`,
    `- Competitors: ${metadata.competitors || '(missing)'}`,
    `- Budget: ${metadata.budget || '(missing)'}`,
    `- Timing: ${metadata.timing || '(missing)'}`,
    `- Geography: ${metadata.geography || '(missing)'}`,
    '',
    "Reply with **confirm** to continue, or edit any field by sending updated values.",
  ].join('\n')
}

function formatGuestModeSelectionPrompt() {
  return [
    '## Mode Selection',
    '',
    'Choose execution mode:',
    '- **interactive**: step-by-step, you type continue',
    '- **autonomous**: runs all remaining agents automatically',
    '',
    "Reply with **interactive** or **autonomous**.",
  ].join('\n')
}

function parseGuestExecutionMode(text: string): 'interactive' | 'autonomous' | null {
  const normalized = text.trim().toLowerCase()
  const interactive = ['interactive', 'interactively']
  const autonomous = ['autonomous', 'auto', 'automatically']
  const hasInteractive = interactive.some((token) => normalized.includes(token))
  const hasAutonomous = autonomous.some((token) => normalized.includes(token))
  if (hasInteractive && !hasAutonomous) return 'interactive'
  if (hasAutonomous && !hasInteractive) return 'autonomous'
  return null
}

function formatSpecialistAnalysis(raw: string | undefined, title: string) {
  const data = parseJsonPayload(raw)
  if (!data) return raw || `No ${title} output was returned.`
  const dict = data as Record<string, unknown>
  const sections: string[] = [`### ${title} Summary`, '']

  for (const key of [
    'key_insights',
    'recommendations',
    'differentiation_opportunities',
    'whitespace_opportunities',
  ]) {
    const value = dict[key]
    if (!Array.isArray(value) || value.length === 0) continue
    sections.push(`**${key.replaceAll('_', ' ')}:**`)
    value.slice(0, 6).forEach((item) => {
      if (item && typeof item === 'object') {
        const map = item as Record<string, unknown>
        sections.push(
          `- ${String(map.opportunity || map.trend || map.campaign || JSON.stringify(item))}`,
        )
      } else {
        sections.push(`- ${String(item)}`)
      }
    })
    sections.push('')
  }

  return sections.join('\n').trim() || raw || `No ${title} output was returned.`
}

function extractSection(markdown: string | undefined, titles: string[]) {
  if (!markdown) return undefined
  for (const title of titles) {
    const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(
      `(?:^|\\n)##\\s*${escaped}\\s*\\n([\\s\\S]*?)(?=\\n##\\s|$)`,
      'i',
    )
    const match = markdown.match(regex)
    if (match?.[1]?.trim()) return match[1].trim()
  }
  return undefined
}

function fallbackSpecialistContent(
  cached: AnalysisMetadata & { final_insights?: string } | undefined,
  kind: 'trend' | 'case' | 'landscape',
) {
  const finalInsights = cached?.final_insights
  if (!finalInsights) return undefined

  if (kind === 'trend') {
    return (
      extractSection(finalInsights, [
        'Key Trends & Opportunities',
        'Trends',
        'Trend Analysis',
      ]) || finalInsights.slice(0, 1200)
    )
  }

  if (kind === 'case') {
    return (
      extractSection(finalInsights, [
        'Competitive Landscape',
        'Case Intelligence',
        'Competitor Analysis',
      ]) || finalInsights.slice(0, 1200)
    )
  }

  return (
    extractSection(finalInsights, [
      'Competitive Landscape',
      'Market Landscape',
      'Landscape Analysis',
    ]) || finalInsights.slice(0, 1200)
  )
}

function formatStepOutput(title: string, content: string | undefined, nextLabel: string) {
  return [
    `## ${title}`,
    '',
    content && content.trim().length > 0 ? content : 'No output was returned for this step.',
    '',
    `Reply with **continue** to run **${nextLabel}**.`,
  ].join('\n')
}

function parseCreatorOption(text: string) {
  const normalized = text.trim().toLowerCase()
  if (!normalized) return null
  if (/\b1\b/.test(normalized) || normalized.includes('tagline')) return '1'
  if (
    /\b2\b/.test(normalized) ||
    normalized.includes('content calendar') ||
    normalized.includes('4-week')
  ) {
    return '2'
  }
  if (/\b3\b/.test(normalized) || normalized.includes('hero ad')) return '3'
  return null
}

function guestOptionOutput(option: '1' | '2' | '3', concepts: string) {
  if (option === '1') {
    return [
      '## Creator Output: Tagline Options',
      '',
      `Generated from current campaign concepts:\n\n${concepts.slice(0, 1200)}`,
      '',
      '- Option A: Bring Korea Home, Every Day.',
      '- Option B: Taste Korea, Live the Culture.',
      '- Option C: From Seoul Trends to Your Table.',
      '- Option D: Your Korean Life Starts at Oseyo.',
      '- Option E: Real Korean Flavor. Right Here.',
    ].join('\n')
  }

  if (option === '2') {
    return [
      '## Creator Output: 4-Week Content Calendar',
      '',
      '### Week 1: Awareness',
      '- Teaser reels + influencer seeding + store mood content',
      '### Week 2: Discovery',
      '- Product explainers + recipe shorts + snack format tests',
      '### Week 3: Engagement',
      '- UGC challenge + creator duets + community repost loop',
      '### Week 4: Conversion',
      '- Bundle pushes + promo creatives + urgency CTA ads',
      '',
      '_Calendar generated from current creator concepts and timing context._',
    ].join('\n')
  }

  return [
    '## Creator Output: Hero Ad Concepts',
    '',
    '1. **From Screen to Shelf**: Recreate iconic K-drama food moments with Oseyo bundles.',
    '2. **K-Food Night Ritual**: Fast-paced social-first montage around ramen, snacks, and late-night routines.',
    '3. **Taste Korea at Home**: Emotional lifestyle narrative linking culture, identity, and everyday meals.',
    '',
    '_Hero concepts generated from current campaign concept set._',
  ].join('\n')
}

function createGuestAssistantMessage(content: string, conversationId: string): Message {
  return {
    id: guestId('msg'),
    conversation_id: conversationId,
    role: 'assistant',
    content,
    message_type: 'analysis',
    created_at: guestNow(),
    metadata: null,
  }
}

async function runGuestEnhancement(content: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/enhance-brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief: content }),
    })
    if (!response.ok) throw new Error('enhancement request failed')
    const data = (await response.json()) as { final_insights?: string }
    if (data.final_insights?.trim()) return data.final_insights
  } catch {
    // fall through to local fallback response
  }

  return [
    'Guest mode is active, so this response is running in local fallback mode.',
    'Connect the backend API at NEXT_PUBLIC_API_URL for full AI analysis.',
    '',
    `You wrote: ${content}`,
  ].join('\n')
}

async function runGuestBriefAnalysis(content: string): Promise<string> {
  const localBriefFallback = [
    '## Brief Analysis Report',
    '',
    'Brief analyzer fallback is active in guest mode.',
    'Connect backend `/api/v1/brief-analyze` for full model-generated brief analysis.',
  ].join('\n')

  try {
    const response = await fetch(`${API_BASE}/api/v1/brief-analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief: content }),
    })
    if (!response.ok) throw new Error('brief analysis request failed')
    const data = (await response.json()) as { brief_analysis?: string }
    const analysis = data.brief_analysis?.trim()
    if (analysis) return analysis
  } catch {
    // fall through
  }

  return localBriefFallback
}

async function runGuestEnhancementDetailed(content: string): Promise<{
  brief_analysis?: string
  trend_analysis?: string
  case_analysis?: string
  landscape_analysis?: string
  creator_concepts?: string
  final_insights: string
}> {
  const localBriefFallback = [
    '# Brief Analysis Report',
    '',
    '## 1. Background & Context',
    '- **Classification:** Missing',
    "- **What's Missing:** Business context, market situation, and campaign rationale are not clearly stated.",
    '- **What Would Make It Complete:** Add campaign background, current market context, and key business drivers.',
    '',
    '## 2. Task & Deliverables',
    '- **Classification:** Partial',
    "- **What's Missing:** Deliverables are not specific (assets, channels, timeline detail, and constraints).",
    '- **What Would Make It Complete:** Define exact deliverables and channel-level expectations.',
    '',
    '## 3. Marketing Objectives & KPIs',
    '- **Classification:** Partial',
    "- **What's Missing:** Objective is present but KPI definitions and measurement plan are missing.",
    '- **What Would Make It Complete:** Add measurable KPIs and success tracking method.',
    '',
    '## ACTION REQUIRED',
    'Please provide missing context, target audience detail, competitor landscape, and KPIs before next agent steps.',
    '',
    '**Do you want to work INTERACTIVELY with AI AGENTS or have the AI AGENTS WORK AUTONOMOUSLY?**',
  ].join('\n')

  try {
    const response = await fetch(`${API_BASE}/api/v1/enhance-brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brief: content }),
    })
    if (!response.ok) throw new Error('enhancement request failed')
    const data = (await response.json()) as {
      brief_analysis?: string
      trend_analysis?: string
      case_analysis?: string
      landscape_analysis?: string
      creator_concepts?: string
      final_insights?: string
    }
    const finalInsights =
      data.final_insights?.trim() ||
      'No final insight was returned by the backend.'
    const derivedTrend = extractSection(finalInsights, ['Key Trends & Opportunities'])
    const derivedCase = extractSection(finalInsights, ['Competitive Landscape'])
    const derivedLandscape = extractSection(finalInsights, ['Competitive Landscape'])

    return {
      brief_analysis: data.brief_analysis || localBriefFallback,
      trend_analysis: data.trend_analysis || derivedTrend,
      case_analysis: data.case_analysis || derivedCase,
      landscape_analysis: data.landscape_analysis || derivedLandscape,
      creator_concepts: data.creator_concepts,
      final_insights: finalInsights,
    }
  } catch {
    return {
      brief_analysis: localBriefFallback,
      creator_concepts: undefined,
      final_insights: await runGuestEnhancement(content),
    }
  }
}

async function guestList() {
  const conversations = await readGuestConversations()
  return conversations.sort((a, b) =>
    b.updated_at.localeCompare(a.updated_at),
  )
}

async function guestCreate(payload: CreateConversationPayload = {}) {
  const now = guestNow()
  const requestedTitle = payload.title?.trim()
  const conversation: Conversation = {
    id: guestId('convo'),
    user_id: GUEST_USER_ID,
    title: requestedTitle ? normalizeConversationTitle(requestedTitle) : 'New Conversation',
    created_at: now,
    updated_at: now,
    messages: [],
  }
  await saveGuestConversation(conversation)
  setGuestRuntime(conversation.id, defaultGuestRuntime())
  await setGuestRuntimeData(conversation.id, defaultGuestRuntimeData(conversation.id))
  return conversation
}

async function guestGet(conversationId: string) {
  const conversation = await getGuestConversationById(conversationId)
  if (!conversation) throw new Error('Conversation not found')
  return conversation
}

async function guestDelete(conversationId: string) {
  await deleteGuestConversationRecord(conversationId)
  await deleteGuestRuntimeData(conversationId)
  const runtime = readGuestRuntimeMap()
  delete runtime[conversationId]
  writeGuestRuntimeMap(runtime)
}

async function guestRename(conversationId: string, payload: UpdateConversationPayload) {
  const nextTitle = normalizeConversationTitle(payload.title)
  const conversation = await getGuestConversationById(conversationId)
  if (!conversation) throw new Error('Conversation not found')

  conversation.title = nextTitle
  conversation.updated_at = guestNow()
  await saveGuestConversation(conversation)
  return conversation
}

async function guestSendMessage(
  conversationId: string,
  payload: SendMessagePayload,
): Promise<Message> {
  const conversation = await getGuestConversationById(conversationId)
  if (!conversation) throw new Error('Conversation not found')

  const now = guestNow()
  const isFirst = (conversation.messages?.length ?? 0) === 0
  const userMessage: Message = {
    id: guestId('msg'),
    conversation_id: conversationId,
    role: 'user',
    content: payload.content,
    message_type: isFirst ? 'interactive_brief' : 'followup',
    created_at: now,
    metadata: null,
  }

  const runtime = getGuestRuntime(conversationId)
  const runtimeData = await getGuestRuntimeData(conversationId)

  let assistantText = ''
  let assistantType: Message['message_type'] = 'followup'
  let metadata: Message['metadata'] = null
  const assistantMessages: Message[] = []

  const pushAssistant = (
    content: string,
    messageType: Message['message_type'] = 'analysis',
    messageMetadata: Message['metadata'] = null,
  ) => {
    const msg = createGuestAssistantMessage(content, conversationId)
    msg.message_type = messageType
    msg.metadata = messageMetadata
    assistantMessages.push(msg)
    return msg
  }

  if (isFirst) {
    const briefAnalysis = await runGuestBriefAnalysis(payload.content)
    const extracted = mergeGuestMetadata(runtime.required_metadata, payload.content)
    runtime.required_metadata = extracted
    const missing = missingGuestMetadata(extracted)

    runtime.pipeline_status = 'waiting_user'
    runtime.current_step = missing.length > 0
      ? 'awaiting_user_metadata'
      : 'awaiting_user_metadata_confirmation'
    runtime.pending_prompt = missing.length > 0
      ? 'Provide required metadata fields.'
      : "Reply with 'confirm' to continue, or edit metadata fields."

    assistantType = 'analysis'
    const briefText = [
      '## Step 1 Complete: Brief Analysis',
      '',
      briefAnalysis,
      '',
      missing.length > 0
        ? formatGuestMissingMetadataPrompt(missing)
        : formatGuestMetadataConfirmation(extracted),
    ].join('\n')
    assistantText = briefText
    metadata = {
      workflow_mode: runtime.mode,
      current_step: runtime.current_step,
      required_metadata: extracted,
      missing_required_metadata: missing,
    }

    appendGuestEvent(runtimeData, conversationId, {
      id: guestId('evt'),
      agent_name: 'brief_analyzer',
      status: 'completed',
      content: briefAnalysis,
      metadata: {},
    })
  } else if (runtime.current_step === 'awaiting_user_metadata') {
    const merged = mergeGuestMetadata(runtime.required_metadata, payload.content)
    runtime.required_metadata = merged
    const missing = missingGuestMetadata(merged)

    assistantType = 'analysis'
    if (missing.length > 0) {
      assistantText = formatGuestMissingMetadataPrompt(missing)
      runtime.current_step = 'awaiting_user_metadata'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = 'Provide required metadata fields.'
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
        missing_required_metadata: missing,
      }
    } else {
      assistantText = formatGuestMetadataConfirmation(merged)
      runtime.current_step = 'awaiting_user_metadata_confirmation'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'confirm' to continue, or edit metadata fields."
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
      }
    }
  } else if (runtime.current_step === 'awaiting_user_metadata_confirmation') {
    const merged = mergeGuestMetadata(runtime.required_metadata, payload.content)
    runtime.required_metadata = merged
    const missing = missingGuestMetadata(merged)
    const normalized = payload.content.trim().toLowerCase()

    assistantType = 'analysis'
    if (missing.length > 0) {
      assistantText = formatGuestMissingMetadataPrompt(missing)
      runtime.current_step = 'awaiting_user_metadata'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = 'Provide required metadata fields.'
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
        missing_required_metadata: missing,
      }
    } else if (METADATA_CONFIRM_WORDS.has(normalized)) {
      assistantText = formatGuestModeSelectionPrompt()
      runtime.current_step = 'awaiting_user_mode_selection'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = 'Choose mode: interactive or autonomous.'
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
      }
    } else {
      assistantText = formatGuestMetadataConfirmation(merged)
      runtime.current_step = 'awaiting_user_metadata_confirmation'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'confirm' to continue, or edit metadata fields."
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
      }
    }
  } else if (runtime.current_step === 'awaiting_user_mode_selection') {
    const merged = mergeGuestMetadata(runtime.required_metadata, payload.content)
    runtime.required_metadata = merged
    const missing = missingGuestMetadata(merged)
    const selectedMode = parseGuestExecutionMode(payload.content)

    assistantType = 'analysis'
    if (missing.length > 0) {
      assistantText = formatGuestMissingMetadataPrompt(missing)
      runtime.current_step = 'awaiting_user_metadata'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = 'Provide required metadata fields.'
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
        missing_required_metadata: missing,
      }
    } else if (selectedMode === 'interactive') {
      runtime.mode = 'interactive'
      runtime.current_step = 'awaiting_user_continue_trend'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'continue' to run Trend Agent."
      assistantText = "Mode set to **interactive**.\n\nReply with **continue** to run **Trend Agent**."
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
      }
    } else if (selectedMode === 'autonomous') {
      runtime.mode = 'autonomous'
      runtime.current_step = 'running_pipeline'
      runtime.pipeline_status = 'running'
      runtime.pending_prompt = null
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
      }

      const firstUser = (conversation.messages ?? []).find((m) => m.role === 'user')
      const briefText = firstUser?.content || payload.content
      const detailed = await runGuestEnhancementDetailed(briefText)
      runtimeData.cached_analysis = detailed

      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'trend_agent',
        status: 'started',
        content: 'Running trend analysis',
        metadata: {},
      })
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'trend_agent',
        status: 'completed',
        content: detailed.trend_analysis || 'Trend analysis completed.',
        metadata: {},
      })
      pushAssistant(
        "## Step 2 Complete: Trend Analysis\n\n" +
          formatSpecialistAnalysis(
            detailed.trend_analysis || fallbackSpecialistContent(detailed, 'trend'),
            'Trend Agent',
          ),
        'analysis',
        { workflow_mode: 'autonomous', current_step: 'step_2_trend' },
      )

      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'case_intelligence',
        status: 'started',
        content: 'Running case intelligence analysis',
        metadata: {},
      })
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'case_intelligence',
        status: 'completed',
        content: detailed.case_analysis || 'Case analysis completed.',
        metadata: {},
      })
      pushAssistant(
        "## Step 3 Complete: Case Intelligence Analysis\n\n" +
          formatSpecialistAnalysis(
            detailed.case_analysis || fallbackSpecialistContent(detailed, 'case'),
            'Case Intelligence',
          ),
        'analysis',
        { workflow_mode: 'autonomous', current_step: 'step_3_case' },
      )

      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'market_landscape',
        status: 'started',
        content: 'Running market landscape analysis',
        metadata: {},
      })
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'market_landscape',
        status: 'completed',
        content: detailed.landscape_analysis || 'Market landscape analysis completed.',
        metadata: {},
      })
      pushAssistant(
        "## Step 4 Complete: Market Landscape Analysis\n\n" +
          formatSpecialistAnalysis(
            detailed.landscape_analysis || fallbackSpecialistContent(detailed, 'landscape'),
            'Market Landscape',
          ),
        'analysis',
        { workflow_mode: 'autonomous', current_step: 'step_4_landscape' },
      )

      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'insight_generator',
        status: 'started',
        content: 'Synthesizing final recommendations',
        metadata: {},
      })
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'insight_generator',
        status: 'completed',
        content: detailed.final_insights,
        metadata: {},
      })
      pushAssistant(
        `## Step 5 Complete: Insight Generation\n\n${detailed.final_insights}`,
        'analysis',
        {
          brief_analysis: detailed.brief_analysis,
          trend_analysis: detailed.trend_analysis,
          case_analysis: detailed.case_analysis,
          landscape_analysis: detailed.landscape_analysis,
          final_insights: detailed.final_insights,
          workflow_mode: 'autonomous',
          current_step: 'step_5_insight',
        },
      )

      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'creator_agent',
        status: 'started',
        content: 'Generating four campaign concepts',
        metadata: {},
      })
      const creatorOutput =
        detailed.creator_concepts ||
        [
          '## Creator Output',
          '',
          'No creator concepts were returned from backend.',
        ].join('\n')
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'creator_agent',
        status: 'completed',
        content: creatorOutput,
        metadata: {},
      })
      pushAssistant(
        `## Step 6 Complete: Creator Output\n\n${creatorOutput}`,
        'analysis',
        {
          brief_analysis: detailed.brief_analysis,
          trend_analysis: detailed.trend_analysis,
          case_analysis: detailed.case_analysis,
          landscape_analysis: detailed.landscape_analysis,
          final_insights: detailed.final_insights,
          creator_concepts: creatorOutput,
          workflow_mode: 'autonomous',
          current_step: 'completed',
        },
      )

      runtime.current_step = 'completed'
      runtime.pipeline_status = 'idle'
      runtime.pending_prompt = null
      assistantText = creatorOutput
      metadata = {
        brief_analysis: detailed.brief_analysis,
        trend_analysis: detailed.trend_analysis,
        case_analysis: detailed.case_analysis,
        landscape_analysis: detailed.landscape_analysis,
        final_insights: detailed.final_insights,
        creator_concepts: creatorOutput,
        workflow_mode: 'autonomous',
        current_step: 'completed',
        required_metadata: merged,
      }
    } else {
      assistantText = formatGuestModeSelectionPrompt()
      runtime.current_step = 'awaiting_user_mode_selection'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = 'Choose mode: interactive or autonomous.'
      metadata = {
        workflow_mode: runtime.mode,
        current_step: runtime.current_step,
        required_metadata: merged,
      }
    }
  } else if (
    runtime.mode === 'interactive' &&
    runtime.current_step !== 'completed' &&
    runtime.current_step !== 'idle'
  ) {
    const normalized = payload.content.trim().toLowerCase()
    if (normalized.includes('interact')) {
      runtime.mode = 'interactive'
    }

    const ensureCachedAnalysis = async () => {
      const needRefresh =
        !runtimeData.cached_analysis ||
        !runtimeData.cached_analysis.trend_analysis ||
        !runtimeData.cached_analysis.case_analysis ||
        !runtimeData.cached_analysis.landscape_analysis

      if (!needRefresh) return
      const firstUser = (conversation.messages ?? []).find((m) => m.role === 'user')
      const briefText = firstUser?.content || payload.content
      const refreshed = await runGuestEnhancementDetailed(briefText)
      runtimeData.cached_analysis = {
        ...runtimeData.cached_analysis,
        ...refreshed,
      }
    }

    if (runtime.current_step === 'awaiting_user_creator_option') {
      await ensureCachedAnalysis()
      const selectedOption = parseCreatorOption(payload.content)
      const normalizedInput = payload.content.trim().toLowerCase()
      if (['done', 'finish', 'complete', 'completed'].includes(normalizedInput)) {
        assistantType = 'analysis'
        assistantText = 'Creator step completed. You can continue with normal chat.'
        runtime.current_step = 'completed'
        runtime.pipeline_status = 'idle'
        runtime.pending_prompt = null
        metadata = {
          brief_analysis: runtimeData.cached_analysis?.brief_analysis,
          trend_analysis: runtimeData.cached_analysis?.trend_analysis,
          case_analysis: runtimeData.cached_analysis?.case_analysis,
          landscape_analysis: runtimeData.cached_analysis?.landscape_analysis,
          final_insights: runtimeData.cached_analysis?.final_insights,
          creator_concepts: runtimeData.cached_analysis?.creator_concepts,
          workflow_mode: 'interactive',
          current_step: 'completed',
        }
      } else if (!selectedOption) {
        assistantType = 'followup'
        assistantText =
          'Creator step is waiting. Reply with **1** (Tagline options), **2** (4-week content calendar), **3** (Hero ad concepts), or **done**.'
        metadata = {
          workflow_mode: 'interactive',
          current_step: runtime.current_step,
        }
      } else {
        const concepts =
          runtimeData.cached_analysis?.creator_concepts ||
          'No creator concepts cached in guest mode.'
        assistantType = 'analysis'
        assistantText = [
          guestOptionOutput(selectedOption as '1' | '2' | '3', concepts),
          '',
          'Reply with **1**, **2**, or **3** for another creator output, or **done** to finish creator step.',
        ].join('\n')
        runtime.current_step = 'awaiting_user_creator_option'
        runtime.pipeline_status = 'waiting_user'
        runtime.pending_prompt =
          "Reply with 1 (Tagline options), 2 (4-week content calendar), or 3 (Hero ad concepts). Reply 'done' to finish."
        metadata = {
          brief_analysis: runtimeData.cached_analysis?.brief_analysis,
          trend_analysis: runtimeData.cached_analysis?.trend_analysis,
          case_analysis: runtimeData.cached_analysis?.case_analysis,
          landscape_analysis: runtimeData.cached_analysis?.landscape_analysis,
          final_insights: runtimeData.cached_analysis?.final_insights,
          creator_concepts: concepts,
          selected_creator_option: selectedOption,
          workflow_mode: 'interactive',
          current_step: 'awaiting_user_creator_option',
        }
        appendGuestEvent(runtimeData, conversationId, {
          id: guestId('evt'),
          agent_name: 'creator_agent',
          status: 'completed',
          content: assistantText,
          metadata: { selected_option: selectedOption },
        })
      }
    } else if (!CONTINUE_WORDS.has(normalized)) {
      assistantType = 'followup'
      assistantText = 'Interactive mode is waiting. Reply with **continue** to run the next step.'
      metadata = {
        workflow_mode: 'interactive',
        current_step: runtime.current_step,
      }
    } else if (runtime.current_step === 'awaiting_user_continue_trend') {
      await ensureCachedAnalysis()
      const trendContent =
        runtimeData.cached_analysis?.trend_analysis ||
        fallbackSpecialistContent(runtimeData.cached_analysis, 'trend')
      assistantType = 'analysis'
      assistantText = formatStepOutput(
        'Step 2 Complete: Trend Analysis',
        formatSpecialistAnalysis(trendContent, 'Trend Agent'),
        'Case Intelligence Agent',
      )
      runtime.current_step = 'awaiting_user_continue_case'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'continue' to run Case Intelligence Agent."
      metadata = {
        brief_analysis: runtimeData.cached_analysis?.brief_analysis,
        trend_analysis: runtimeData.cached_analysis?.trend_analysis,
        workflow_mode: 'interactive',
        current_step: runtime.current_step,
      }
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'trend_agent',
        status: 'completed',
        content: trendContent || 'Trend analysis completed.',
        metadata: {},
      })
    } else if (runtime.current_step === 'awaiting_user_continue_case') {
      await ensureCachedAnalysis()
      const caseContent =
        runtimeData.cached_analysis?.case_analysis ||
        fallbackSpecialistContent(runtimeData.cached_analysis, 'case')
      assistantType = 'analysis'
      assistantText = formatStepOutput(
        'Step 3 Complete: Case Intelligence Analysis',
        formatSpecialistAnalysis(caseContent, 'Case Intelligence'),
        'Market Landscape Agent',
      )
      runtime.current_step = 'awaiting_user_continue_landscape'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'continue' to run Market Landscape Agent."
      metadata = {
        case_analysis: runtimeData.cached_analysis?.case_analysis,
        workflow_mode: 'interactive',
        current_step: runtime.current_step,
      }
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'case_intelligence',
        status: 'completed',
        content: caseContent || 'Case analysis completed.',
        metadata: {},
      })
    } else if (runtime.current_step === 'awaiting_user_continue_landscape') {
      await ensureCachedAnalysis()
      const landscapeContent =
        runtimeData.cached_analysis?.landscape_analysis ||
        fallbackSpecialistContent(runtimeData.cached_analysis, 'landscape')
      assistantType = 'analysis'
      assistantText = formatStepOutput(
        'Step 4 Complete: Market Landscape Analysis',
        formatSpecialistAnalysis(landscapeContent, 'Market Landscape'),
        'Insight Generator',
      )
      runtime.current_step = 'awaiting_user_continue_insight'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'continue' to run Insight Generator."
      metadata = {
        landscape_analysis: runtimeData.cached_analysis?.landscape_analysis,
        workflow_mode: 'interactive',
        current_step: runtime.current_step,
      }
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'market_landscape',
        status: 'completed',
        content: landscapeContent || 'Market landscape analysis completed.',
        metadata: {},
      })
    } else if (runtime.current_step === 'awaiting_user_continue_insight') {
      await ensureCachedAnalysis()
      const insights =
        runtimeData.cached_analysis?.final_insights ||
        'No final synthesis available from guest runtime.'
      assistantType = 'analysis'
      assistantText = formatStepOutput(
        'Step 5 Complete: Insight Generation',
        insights,
        'Creator Agent',
      )
      runtime.current_step = 'awaiting_user_continue_creator'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt = "Reply with 'continue' to run Creator Agent."
      metadata = {
        brief_analysis: runtimeData.cached_analysis?.brief_analysis,
        trend_analysis: runtimeData.cached_analysis?.trend_analysis,
        case_analysis: runtimeData.cached_analysis?.case_analysis,
        landscape_analysis: runtimeData.cached_analysis?.landscape_analysis,
        final_insights: runtimeData.cached_analysis?.final_insights,
        workflow_mode: 'interactive',
        current_step: runtime.current_step,
      }
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'insight_generator',
        status: 'completed',
        content: insights,
        metadata: {},
      })
    } else if (runtime.current_step === 'awaiting_user_continue_creator') {
      await ensureCachedAnalysis()
      const concepts =
        runtimeData.cached_analysis?.creator_concepts ||
        [
          '## Creator Output',
          '',
          'Guest mode did not receive structured Creator output from backend.',
          'Reply with 1 (Tagline options), 2 (4-week content calendar), or 3 (Hero ad concepts).',
        ].join('\n')
      assistantType = 'analysis'
      assistantText = concepts
      runtime.current_step = 'awaiting_user_creator_option'
      runtime.pipeline_status = 'waiting_user'
      runtime.pending_prompt =
        'Reply with 1 (Tagline options), 2 (4-week content calendar), or 3 (Hero ad concepts).'
      metadata = {
        brief_analysis: runtimeData.cached_analysis?.brief_analysis,
        trend_analysis: runtimeData.cached_analysis?.trend_analysis,
        case_analysis: runtimeData.cached_analysis?.case_analysis,
        landscape_analysis: runtimeData.cached_analysis?.landscape_analysis,
        final_insights: runtimeData.cached_analysis?.final_insights,
        creator_concepts: concepts,
        workflow_mode: 'interactive',
        current_step: runtime.current_step,
      }
      appendGuestEvent(runtimeData, conversationId, {
        id: guestId('evt'),
        agent_name: 'creator_agent',
        status: 'completed',
        content: concepts,
        metadata: {},
      })
    } else {
      assistantType = 'analysis'
      assistantText = 'Interactive flow is complete.'
      runtime.current_step = 'completed'
      runtime.pipeline_status = 'idle'
      runtime.pending_prompt = null
      metadata = {
        brief_analysis: runtimeData.cached_analysis?.brief_analysis,
        trend_analysis: runtimeData.cached_analysis?.trend_analysis,
        case_analysis: runtimeData.cached_analysis?.case_analysis,
        landscape_analysis: runtimeData.cached_analysis?.landscape_analysis,
        final_insights: runtimeData.cached_analysis?.final_insights,
        creator_concepts: runtimeData.cached_analysis?.creator_concepts,
        workflow_mode: 'interactive',
        current_step: 'completed',
      }
    }
  } else {
    assistantType = userMessage.message_type === 'interactive_brief' ? 'analysis' : 'followup'
    assistantText = await runGuestEnhancement(payload.content)
  }

  if (assistantMessages.length === 0) {
    pushAssistant(assistantText, assistantType, metadata)
  }
  const assistantMessage = assistantMessages[assistantMessages.length - 1]

  const existing = conversation.messages ?? []
  conversation.messages = [...existing, userMessage, ...assistantMessages]
  if (
    conversation.title === 'New Conversation' &&
    userMessage.content.trim().length > 0
  ) {
    const cleaned = userMessage.content.trim().replace(/\s+/g, ' ')
    conversation.title = cleaned.length > 60 ? `${cleaned.slice(0, 57)}...` : cleaned
  }
  conversation.updated_at = now
  runtimeData.updated_at = now
  await saveGuestConversation(conversation)
  setGuestRuntime(conversationId, runtime)
  await setGuestRuntimeData(conversationId, runtimeData)
  return assistantMessage
}

async function guestListAgents(): Promise<AgentListItem[]> {
  return [
    {
      id: 'brief_analyzer',
      name: 'Brief Analyzer',
      description: 'Analyze brief completeness and identify missing gaps.',
      display_order: 1,
      enabled: true,
    },
    {
      id: 'trend_agent',
      name: 'Trend Agent',
      description: 'Search and summarize relevant market trends.',
      display_order: 2,
      enabled: true,
    },
    {
      id: 'case_intelligence',
      name: 'Case Intelligence',
      description: 'Find comparable campaigns and competitor examples.',
      display_order: 3,
      enabled: true,
    },
    {
      id: 'market_landscape',
      name: 'Market Landscape',
      description: 'Map positioning and whitespace opportunities.',
      display_order: 4,
      enabled: true,
    },
    {
      id: 'insight_generator',
      name: 'Insight Generator',
      description: 'Synthesize all outputs into final strategic guidance.',
      display_order: 5,
      enabled: true,
    },
    {
      id: 'creator_agent',
      name: 'Creator Agent',
      description: 'Generate campaign concepts and execution assets.',
      display_order: 6,
      enabled: true,
    },
  ]
}

async function guestGetState(conversationId: string): Promise<ConversationState> {
  const runtime = getGuestRuntime(conversationId)
  return {
    conversation_id: conversationId,
    mode: runtime.mode,
    current_step: runtime.current_step,
    pipeline_status: runtime.pipeline_status,
    pending_prompt: runtime.pending_prompt,
    updated_at: runtime.updated_at,
  }
}

async function guestUpdateState(
  conversationId: string,
  payload: ConversationStateUpdatePayload,
): Promise<ConversationState> {
  const runtime = getGuestRuntime(conversationId)
  runtime.mode = payload.mode ?? runtime.mode
  runtime.current_step = (payload.current_step as GuestStep | undefined) ?? runtime.current_step
  runtime.pipeline_status = payload.pipeline_status ?? runtime.pipeline_status
  runtime.pending_prompt = payload.pending_prompt ?? runtime.pending_prompt
  setGuestRuntime(conversationId, runtime)
  return {
    conversation_id: conversationId,
    mode: runtime.mode,
    current_step: runtime.current_step,
    pipeline_status: runtime.pipeline_status,
    pending_prompt: runtime.pending_prompt,
    updated_at: runtime.updated_at,
  }
}

async function guestListAgentEvents(
  conversationId: string,
  options: { limit?: number; after?: string } = {},
): Promise<AgentEvent[]> {
  const runtimeData = await getGuestRuntimeData(conversationId)
  let events = runtimeData.events
  if (options.after) {
    events = events.filter((e) => e.created_at > options.after!)
  }
  const limit = options.limit ?? 200
  return events.slice(-limit)
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken()
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (!token && isGuestModeEnabled) {
    const guestSessionId = getGuestSessionId()
    if (guestSessionId) headers.set('X-Guest-Id', guestSessionId)
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const data = await response.json()
      if (typeof data?.detail === 'string') message = data.detail
    } catch {
      // Keep default message when response body is not JSON.
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const conversationsApi = {
  async list() {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<Conversation[]>('/api/v1/conversations')
      } catch {
        return guestList()
      }
    }
    return apiRequest<Conversation[]>('/api/v1/conversations')
  },

  async create(payload: CreateConversationPayload = {}) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<Conversation>('/api/v1/conversations', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
      } catch {
        return guestCreate(payload)
      }
    }
    return apiRequest<Conversation>('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async get(conversationId: string) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<Conversation>(`/api/v1/conversations/${conversationId}`)
      } catch {
        return guestGet(conversationId)
      }
    }
    return apiRequest<Conversation>(`/api/v1/conversations/${conversationId}`)
  },

  async sendMessage(conversationId: string, payload: SendMessagePayload) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<Message>(`/api/v1/conversations/${conversationId}/messages`, {
          method: 'POST',
          body: JSON.stringify(payload),
        })
      } catch {
        return guestSendMessage(conversationId, payload)
      }
    }
    return apiRequest<Message>(`/api/v1/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async delete(conversationId: string) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<void>(`/api/v1/conversations/${conversationId}`, {
          method: 'DELETE',
        })
      } catch {
        return guestDelete(conversationId)
      }
    }
    return apiRequest<void>(`/api/v1/conversations/${conversationId}`, {
      method: 'DELETE',
    })
  },

  async rename(conversationId: string, payload: UpdateConversationPayload) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<Conversation>(`/api/v1/conversations/${conversationId}`, {
          method: 'PATCH',
          body: JSON.stringify({
            title: normalizeConversationTitle(payload.title),
          }),
        })
      } catch {
        return guestRename(conversationId, payload)
      }
    }
    return apiRequest<Conversation>(`/api/v1/conversations/${conversationId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        title: normalizeConversationTitle(payload.title),
      }),
    })
  },

  async listAgents() {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<AgentListItem[]>('/api/v1/agents')
      } catch {
        return guestListAgents()
      }
    }
    return apiRequest<AgentListItem[]>('/api/v1/agents')
  },

  async getState(conversationId: string) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<ConversationState>(`/api/v1/conversations/${conversationId}/state`)
      } catch {
        return guestGetState(conversationId)
      }
    }
    return apiRequest<ConversationState>(`/api/v1/conversations/${conversationId}/state`)
  },

  async updateState(conversationId: string, payload: ConversationStateUpdatePayload) {
    const token = await getAccessToken()
    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<ConversationState>(`/api/v1/conversations/${conversationId}/state`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
      } catch {
        return guestUpdateState(conversationId, payload)
      }
    }
    return apiRequest<ConversationState>(`/api/v1/conversations/${conversationId}/state`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },

  async listAgentEvents(
    conversationId: string,
    options: { limit?: number; after?: string } = {},
  ) {
    const token = await getAccessToken()
    const params = new URLSearchParams()
    if (options.limit) params.set('limit', String(options.limit))
    if (options.after) params.set('after', options.after)
    const query = params.toString()

    if (!token && isGuestModeEnabled) {
      try {
        return await apiRequest<AgentEvent[]>(
          `/api/v1/conversations/${conversationId}/events${query ? `?${query}` : ''}`,
        )
      } catch {
        return guestListAgentEvents(conversationId, options)
      }
    }

    return apiRequest<AgentEvent[]>(
      `/api/v1/conversations/${conversationId}/events${query ? `?${query}` : ''}`,
    )
  },
}
