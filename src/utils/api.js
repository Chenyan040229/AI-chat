import { useSettingStore } from '@/stores/setting'

const API_BASE_URL = 'https://api.deepseek.com' // 去掉 /v3

/**
 * 构建多模态消息内容
 * 文字 + 图片都以数组形式发送给 DeepSeek
 * @param {string} text - 用户文字
 * @param {Array} images - Base64 图片列表
 * @param {Array} fileTexts - 文件文字列表
 * @returns {Array} content 数组
 */
function buildMessageContent(text, images = [], fileTexts = []) {
  const content = []

  // 添加文件文字
  if (fileTexts.length > 0) {
    fileTexts.forEach(f => {
      content.push({
        type: 'text',
        text: `[文件: ${f.name}]\n${f.text}`
      })
    })
  }

  // 添加用户文字
  if (text && text.trim() !== '') {
    content.push({
      type: 'text',
      text
    })
  }

  // 添加图片
  if (images.length > 0) {
    images.forEach(img => {
      content.push({
        type: 'image_url',
        image_url: {
          url: img.base64
        }
      })
    })
  }

  return content
}

/**
 * 创建聊天完成请求
 */
export const createChatCompletion = async (messages, options = {}) => {
  const settingStore = useSettingStore()

  const payload = {
    model: settingStore.settings.model,
    messages,
    stream: settingStore.settings.stream,
    max_tokens: settingStore.settings.maxTokens,
  }

  const isReasoner = settingStore.settings.model.includes('reasoner')
  if (!isReasoner) {
    payload.temperature = settingStore.settings.temperature
    payload.top_p = settingStore.settings.topP
  }

  const response = await fetch(`${API_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${settingStore.settings.apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: options.signal,
  })

  if (!response.ok) {
    let errorDetail = ''
    try {
      const err = await response.json()
      errorDetail = err?.error?.message || JSON.stringify(err)
    } catch (e) {
      errorDetail = await response.text()
    }
    throw new Error(`API错误 ${response.status}: ${errorDetail}`)
  }

  return response
}

/**
 * 流式聊天处理（支持文字+图片+文件）
 */
export async function streamChatWithEnhancements(
  userMessage,
  historyMessages = [],
  onChunk = () => { },
  options = {}
) {
  const images = options.images || []
  const fileTexts = options.fileTexts || []
  const signal = options.signal

  const userContent = buildMessageContent(userMessage, images, fileTexts)

  const messages = [
    { role: 'system', content: '你是一个 helpful 的 AI 助手。' },

    // 过滤历史消息
    ...historyMessages.filter(m => {
      if (!m.content) return false
      if (typeof m.content === 'string') return m.content.trim() !== ''
      if (Array.isArray(m.content)) return m.content.length > 0
      return true
    }),

    // 用户消息（数组形式，多模态）
    { role: 'user', content: userContent },
  ]

  const response = await createChatCompletion(messages, { signal })

  // 非流式模式：直接解析 JSON
  if (!useSettingStore().settings.stream) {
    const data = await response.json()
    const content = data.choices[0].message.content || ''
    const reasoning = data.choices[0].message.reasoning_content || ''
    if (content) onChunk(content, content, 'content')
    if (reasoning) onChunk(reasoning, reasoning, 'reasoning')
    return { content, reasoning_content: reasoning }
  }

  // 流式模式：逐 chunk 解析 SSE
  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  let accumulatedContent = ''
  let accumulatedReasoning = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      if (line.includes('[DONE]')) continue

      try {
        const data = JSON.parse(line.replace('data: ', ''))
        const delta = data?.choices?.[0]?.delta

        if (delta?.content) {
          accumulatedContent += delta.content
          onChunk(delta.content, accumulatedContent, 'content')
        }

        if (delta?.reasoning_content) {
          accumulatedReasoning += delta.reasoning_content
          onChunk(delta.reasoning_content, accumulatedReasoning, 'reasoning')
        }
      } catch (e) {
        // 忽略解析错误
      }
    }
  }

  return {
    content: accumulatedContent,
    reasoning_content: accumulatedReasoning,
  }
}