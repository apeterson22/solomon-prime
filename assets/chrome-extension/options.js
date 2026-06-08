import { deriveRelayToken } from './background-utils.js'
import { classifyRelayCheckException, classifyRelayCheckResponse } from './options-validation.js'

const DEFAULT_PORT = 18792

function clampPort(value) {
  const n = Number.parseInt(String(value || ''), 10)
  if (!Number.isFinite(n)) return DEFAULT_PORT
  if (n <= 0 || n > 65535) return DEFAULT_PORT
  return n
}

function updateRelayUrl(port) {
  const el = document.getElementById('relay-url')
  if (!el) return
  el.textContent = `http://127.0.0.1:${port}/`
}

function setStatus(kind, message) {
  const status = document.getElementById('status')
  if (!status) return
  status.dataset.kind = kind || ''
  status.textContent = message || ''
}

async function checkRelayReachable(port, token) {
  const url = `http://127.0.0.1:${port}/json/version`
  const trimmedToken = String(token || '').trim()
  if (!trimmedToken) {
    setStatus('error', 'Gateway token required. Save your gateway token to connect.')
    return
  }
  try {
    const relayToken = await deriveRelayToken(trimmedToken, port)
    // Delegate the fetch to the background service worker to bypass
    // CORS preflight on the custom x-openclaw-relay-token header.
    const res = await chrome.runtime.sendMessage({
      type: 'relayCheck',
      url,
      token: relayToken,
    })
    const result = classifyRelayCheckResponse(res, port)
    if (result.action === 'throw') throw new Error(result.error)
    setStatus(result.kind, result.message)
  } catch (err) {
    const result = classifyRelayCheckException(err, port)
    setStatus(result.kind, result.message)
  }
}

const DEFAULT_DISCORD_LINK = 'https://discord.com/invite/clawd'

function normalizeDiscordLink(raw) {
  const v = String(raw || '').trim()
  if (!v) return DEFAULT_DISCORD_LINK
  try {
    const u = new URL(v)
    if (u.protocol === 'http:' || u.protocol === 'https:') return u.toString()
  } catch {}
  return DEFAULT_DISCORD_LINK
}

async function load() {
  const stored = await chrome.storage.local.get(['relayPort', 'gatewayToken', 'discordLink'])
  const port = clampPort(stored.relayPort)
  const token = String(stored.gatewayToken || '').trim()
  const discordLink = normalizeDiscordLink(stored.discordLink)
  document.getElementById('port').value = String(port)
  document.getElementById('token').value = token
  document.getElementById('discordLink').value = discordLink
  updateRelayUrl(port)
  await checkRelayReachable(port, token)
}

async function save() {
  const portInput = document.getElementById('port')
  const tokenInput = document.getElementById('token')
  const discordLinkInput = document.getElementById('discordLink')
  const port = clampPort(portInput.value)
  const token = String(tokenInput.value || '').trim()
  const discordLink = normalizeDiscordLink(discordLinkInput.value)
  await chrome.storage.local.set({ relayPort: port, gatewayToken: token, discordLink })
  portInput.value = String(port)
  tokenInput.value = token
  discordLinkInput.value = discordLink
  updateRelayUrl(port)
  await checkRelayReachable(port, token)
}

async function joinDiscord() {
  const stored = await chrome.storage.local.get(['discordLink'])
  const link = normalizeDiscordLink(stored.discordLink || document.getElementById('discordLink').value)
  await chrome.storage.local.set({ discordLink: link })
  window.open(link, '_blank', 'noopener,noreferrer')
}

document.getElementById('save').addEventListener('click', () => void save())
document.getElementById('joinDiscord').addEventListener('click', () => void joinDiscord())
void load()
