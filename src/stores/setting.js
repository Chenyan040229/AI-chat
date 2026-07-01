import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingStore = defineStore(
  'llm-setting',
  () => {
    const settings = ref({
      model: 'deepseek-chat',
      apiKey: '',
      stream: true,
      maxTokens: 4096,
      temperature: 0.7,
      topP: 0.7,
      topK: 50,
    })

    return {
      settings,
    }
  },
  {
    persist: true,
  },
)

export const modelOptions = [
  {
    label: 'DeepSeek-R1',
    value: 'deepseek-reasoner',
    maxTokens: 16384,
  },
  {
    label: 'DeepSeek-V3',
    value: 'deepseek-chat',
    maxTokens: 8192,
  },
]
