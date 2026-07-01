<script setup>
import ChatInput from '@/components/ChatInput.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import { Plus } from '@element-plus/icons-vue'
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { messageHandler } from '@/utils/messageHandler'
import { streamChatWithEnhancements } from '@/utils/api'
import { useSettingStore } from '@/stores/setting'
import SettingsPanel from '@/components/SettingsPanel.vue'
import PopupMenu from '@/components/PopupMenu.vue'
import DialogEdit from '@/components/DialogEdit.vue'
import { useRouter } from 'vue-router'

// 获取聊天消息
const chatStore = useChatStore()
const currentMessages = computed(() => chatStore.currentMessages)
const isLoading = computed(() => chatStore.isLoading)
const settingStore = useSettingStore()

// 获取消息容器
const messagesContainer = ref(null)

// 监听消息变化，滚动到底部
watch(
  currentMessages,
  () => {
    nextTick(() => {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    })
  },
  { deep: true },
)

onMounted(() => {
  nextTick(() => {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
  if (chatStore.conversations.length === 0) {
    chatStore.createConversation()
  }
})

// 发送消息（支持图片和文件）
const handleSend = async (messageContent) => {
  try {
    // 添加用户消息（显示文字）
    chatStore.addMessage(
      messageHandler.formatMessage('user', messageContent.text, '', messageContent.files),
    )
    chatStore.addMessage(messageHandler.formatMessage('assistant', '', ''))

    chatStore.setIsLoading(true)
    chatStore.resetPaused()
    const lastMessage = chatStore.getLastMessage()
    lastMessage.loading = true

    const controller = new AbortController()
    chatStore.setAbortController(controller)

    const historyMessages = chatStore.currentMessages
      .slice(0, -2)
      .filter((msg) => msg.content && msg.content.trim() !== '')
      .map(({ role, content }) => ({ role, content }))

    // 调用 API，传递图片和文件内容
    await streamChatWithEnhancements(
      messageContent.text,
      historyMessages,
      (chunk, accumulated, type) => {
        if (type === 'content') {
          chatStore.updateLastMessage(
            accumulated,
            lastMessage.reasoning_content || '',
            lastMessage.completion_tokens || 0,
            lastMessage.speed || 0
          )
        } else if (type === 'reasoning') {
          chatStore.updateLastMessage(
            lastMessage.content || '',
            accumulated,
            lastMessage.completion_tokens || 0,
            lastMessage.speed || 0
          )
        }
      },
      {
        signal: controller.signal,
        images: messageContent.images || [],
        fileTexts: messageContent.fileTexts || [],
      }
    )

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('用户暂停了生成')
    } else {
      console.error('Failed to send message:', error)
      const msg = error.message || ''
      if (msg.includes('401')) {
        chatStore.updateLastMessage('❌ API Key 无效或已过期，请在设置中检查。')
      } else if (msg.includes('402') || msg.includes('insufficient_balance')) {
        chatStore.updateLastMessage('❌ 账户余额不足，请前往 DeepSeek 平台充值。')
      } else if (msg.includes('429')) {
        chatStore.updateLastMessage('❌ 请求过于频繁，请稍后再试。')
      } else if (msg.includes('400')) {
        chatStore.updateLastMessage(`❌ 请求参数错误: ${msg}`)
      } else if (msg.includes('500') || msg.includes('502') || msg.includes('503')) {
        chatStore.updateLastMessage('❌ AI 服务暂时不可用，请稍后重试。')
      } else if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
        chatStore.updateLastMessage('❌ 网络连接失败，请检查网络。')
      } else {
        chatStore.updateLastMessage(`❌ ${msg}`)
      }
    }
  } finally {
    chatStore.setIsLoading(false)
    const lastMessage = chatStore.getLastMessage()
    lastMessage.loading = false
  }
}

// 重新生成
const handleRegenerate = async () => {
  try {
    const lastUserMessage = chatStore.currentMessages[chatStore.currentMessages.length - 2]
    chatStore.currentMessages.splice(-2, 2)
    await handleSend({ text: lastUserMessage.content, files: lastUserMessage.files })
  } catch (error) {
    console.error('Failed to regenerate message:', error)
  }
}

// 抽屉引用
const settingDrawer = ref(null)
const popupMenu = ref(null)

// 新建对话
const handleNewChat = () => {
  chatStore.createConversation()
}

// 获取当前对话标题
const currentTitle = computed(() => chatStore.currentConversation?.title || 'LLM Chat')
const formatTitle = (title) => {
  return title.length > 4 ? title.slice(0, 4) + '...' : title
}

// 对话框组件
const dialogEdit = ref(null)

// 路由
const router = useRouter()
const handleBack = async () => {
  router.push('/')
}
</script>

<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-left">
        <PopupMenu ref="popupMenu" />
        <el-button class="new-chat-btn" :icon="Plus" @click="handleNewChat">新对话</el-button>
        <div class="divider"></div>
        <div class="title-wrapper">
          <h1 class="chat-title">{{ formatTitle(currentTitle) }}</h1>
          <button
            class="edit-btn"
            @click="dialogEdit.openDialog(chatStore.currentConversationId, 'edit')"
          >
            <img src="@/assets/photo/编辑.png" alt="edit" />
          </button>
        </div>
      </div>

      <div class="header-right">
        <el-tooltip content="设置" placement="top">
          <button class="action-btn" @click="settingDrawer.openDrawer()">
            <img src="@/assets/photo/设置.png" alt="settings" />
          </button>
        </el-tooltip>
        <el-tooltip content="回到首页" placement="top">
          <button class="action-btn" @click="handleBack">
            <img src="@/assets/photo/返回.png" alt="back" />
          </button>
        </el-tooltip>
      </div>
    </div>

    <div class="messages-container" ref="messagesContainer">
      <template v-if="currentMessages.length > 0">
        <chat-message
          v-for="(message, index) in currentMessages"
          :key="message.id"
          :message="message"
          :is-last-assistant-message="
            index === currentMessages.length - 1 && message.role === 'assistant'
          "
          @regenerate="handleRegenerate"
        />
      </template>
      <div v-else class="empty-state">
        <div class="empty-content">
          <img src="@/assets/photo/对话.png" alt="chat" class="empty-icon" />
          <h2>开始对话吧</h2>
          <p>有什么想和我聊的吗？</p>
        </div>
      </div>
    </div>

    <div class="chat-input-container">
      <chat-input :loading="isLoading" @send="handleSend" />
    </div>

    <SettingsPanel ref="settingDrawer" />
    <DialogEdit ref="dialogEdit" />
  </div>
</template>

<style lang="scss" scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: var(--bg-color);
  border-bottom: 1px solid #ffffff;

  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;

    .action-btn {
      width: 2rem;
      height: 2rem;
      padding: 0;
      border: none;
      background: none;
      cursor: pointer;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;

      img {
        width: 1.4rem;
        height: 1.4rem;
        opacity: 1;
        transition: filter 0.2s;
      }

      &:hover {
        background-color: rgba(0, 0, 0, 0.05);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      }
    }

    .new-chat-btn {
      font-size: 0.8rem;
      height: 2rem;
      padding: 0rem 0.5rem;
      display: inline-flex;
      align-items: center;
      line-height: 1;
      border-radius: 9999px;
      border: 1px solid #3f7af1;
      background-color: #ffffff;
      color: #3f7af1;

      &:hover {
        background-color: #3f7af1;
        border-color: #3f7af1;
        color: #ffffff;
      }

      :deep(.el-icon) {
        margin-right: 4px;
        font-size: 0.875rem;
      }
    }

    .divider {
      height: 1.5rem;
      width: 1px;
      background-color: #e5e7eb;
      margin: 0 0.2rem;
    }

    .title-wrapper {
      position: relative;
      display: flex;
      align-items: center;
      gap: 0.5rem;

      .chat-title {
        margin: 0;
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--text-color-primary);
      }

      .edit-btn {
        opacity: 0;
        width: 0.9rem;
        height: 0.9rem;
        padding: 0;
        border: none;
        background: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: opacity 0.2s ease;

        img {
          width: 100%;
          height: 100%;
        }
      }

      &:hover {
        .edit-btn {
          opacity: 1;
        }
      }
    }
  }

  .header-right {
    display: flex;
    gap: 0.5rem;

    .action-btn {
      width: 2rem;
      height: 2rem;
      padding: 0;
      border: none;
      background: none;
      cursor: pointer;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;

      img {
        width: 1.25rem;
        height: 1.25rem;
        opacity: 1;
        transition: filter 0.2s;
      }

      &:hover {
        background-color: rgba(0, 0, 0, 0.05);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

        img {
          filter: brightness(0.4);
        }
      }
    }
  }
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.6rem;
  background-color: var(--bg-color-secondary);
  max-width: 796px;
  min-width: 0;
  margin: 0 auto;
  width: 100%;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: #ddd;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background-color: transparent;
  }
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;

  .empty-content {
    text-align: center;

    .empty-icon {
      width: 64px;
      height: 64px;
      opacity: 0.6;
      margin-bottom: 1.5rem;
    }

    h2 {
      font-size: 1.5rem;
      font-weight: 500;
      color: var(--text-color-primary);
      margin-bottom: 0.5rem;
    }

    p {
      font-size: 1rem;
      color: var(--text-color-secondary);
      margin: 0;
    }
  }
}

.chat-input-container {
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--bg-color);
  z-index: 10;
  padding: 0.6rem;
  max-width: 796px;
  margin: 0 auto;
  width: 100%;
}
</style>