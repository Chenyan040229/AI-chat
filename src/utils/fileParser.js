/**
 * 文件解析工具（DeepSeek多模态正确版）
 */

import * as pdfjsLib from 'pdfjs-dist'
import mammoth from 'mammoth'

// ======================
// PDF worker
// ======================
pdfjsLib.GlobalWorkerOptions.workerSrc =
  `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`

// ======================
// PDF解析
// ======================
export async function parsePDF(file) {
  try {
    const arrayBuffer = await file.arrayBuffer()

    const pdf = await pdfjsLib.getDocument({
      data: arrayBuffer,
      verbosity: 0,
    }).promise

    let text = ''

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i)
      const content = await page.getTextContent()

      const pageText = content.items
        .map(item => item.str)
        .join(' ')
        .replace(/\s+/g, ' ')
        .trim()

      if (pageText) text += pageText + '\n'
    }

    return text.trim() || '[PDF无文本]'

  } catch (err) {
    console.error('PDF解析失败:', err)
    throw err
  }
}

// ======================
// Word
// ======================
export async function parseWord(file) {
  const arrayBuffer = await file.arrayBuffer()
  const result = await mammoth.extractRawText({ arrayBuffer })
  return result.value.trim()
}

// ======================
// TXT
// ======================
export async function parseTXT(file) {
  return (await file.text()).trim()
}

// ======================
// 单文件入口
// ======================
export async function parseFile(file) {
  const name = file.name.toLowerCase()

  if (name.endsWith('.pdf')) return parsePDF(file)
  if (name.endsWith('.docx')) return parseWord(file)
  if (name.endsWith('.txt')) return parseTXT(file)

  throw new Error('不支持的文件格式')
}

// ======================
// base64
// ======================
export async function imageToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('图片读取失败'))
    reader.readAsDataURL(file)
  })
}

// ======================
// AI OCR Prompt（关键）
// ======================
function buildOCRPrompt(name) {
  return `请识别图片中的所有文字内容，只返回文字，不要解释。图片：${name}`
}

// ======================
// 🚨 核心修复：parseFiles
// ======================
export async function parseFiles(files) {
  const images = []
  const fileTexts = []

  for (const file of files) {
    try {
      const raw = file.raw || file

      // ======================
      // 图片（关键修复点）
      // ======================
      const isImage =
        file.type?.startsWith('image/') ||
        file.type === 'image' ||
        file.type?.includes('image')

      if (isImage) {
        const base64 = await imageToBase64(raw)

        images.push({
          name: file.name,
          base64, // ✔ 必须带给DeepSeek
        })

        // ⚠️ 关键：只放提示词（但图片必须单独发送）
        fileTexts.push({
          name: file.name,
          text: buildOCRPrompt(file.name),
        })

        continue
      }

      // ======================
      // 普通文件
      // ======================
      const text = await parseFile(raw)

      fileTexts.push({
        name: file.name,
        text,
      })

    } catch (err) {
      console.error('解析失败:', file.name, err)

      fileTexts.push({
        name: file.name,
        text: `[解析失败: ${err.message}]`,
      })
    }
  }

  return {
    images,
    fileTexts,
  }
}