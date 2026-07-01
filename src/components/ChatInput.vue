<script setup>
import { ref } from 'vue'
import { Close, Document } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { parseFiles } from '@/utils/fileParser'

// 输入框的值，使用 ref 实现响应式
const inputValue = ref('')
const fileList = ref([]) // 存储上传的文件列表
const chatStore = useChatStore()
const isParsing = ref(false) // 文件解析状态

// 定义组件的 props，接收 loading 状态
const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
})

// 定义组件的事件，这里声明了一个 send 事件
const emit = defineEmits(['send'])

// 处理发送消息的方法
const handleSend = async () => {
  // 必须有文字才能发送
  if (!inputValue.value.trim() || props.loading || isParsing.value) return

  isParsing.value = true

  try {
    // 解析文件内容
    const { images, fileTexts } = await parseFiles(fileList.value)

    // 构建消息对象
    const messageContent = {
      text: inputValue.value.trim(),
      images: images, // Base64 图片列表
      fileTexts: fileTexts, // 文件文字内容列表
    }

    // 触发 send 事件，将消息内容作为参数传递
    emit('send', messageContent)

    // 清空输入框和文件列表
    inputValue.value = ''
    fileList.value = []
  } catch (error) {
    console.error('文件解析失败:', error)
  } finally {
    isParsing.value = false
  }
}

// 处理暂停生成
const handleStop = () => {
  chatStore.pauseGeneration()
}

// 处理换行的方法（Shift + Enter）
const handleNewline = (e) => {
  e.preventDefault()
  inputValue.value += '\n'
}

// 处理文件上传
const handleFileUpload = (uploadFile) => {
  // 确保获取到的是文件对象
  const file = uploadFile.raw
  if (!file) return false

  fileList.value.push({
    name: file.name,
    url: URL.createObjectURL(file),
    type: file.type.startsWith('image/') ? 'image' : 'file',
    size: file.size,
    raw: file, // 保存原始 File 对象，用于后续解析
  })
  return false // 阻止自动上传
}

// 移除文件
const handleFileRemove = (file) => {
  const index = fileList.value.findIndex((item) => item.url === file.url)
  if (index !== -1) {
    URL.revokeObjectURL(fileList.value[index].url) //释放创建该文件的临时URL
    fileList.value.splice(index, 1)
  }
}
</script>

<template>
  <div class="chat-input-wrapper">
    <!-- 文件预览区域 -->
    <div v-if="fileList.length > 0" class="preview-area">
      <div v-for="file in fileList" :key="file.url" class="preview-item">
        <!-- 图片预览 -->
        <div v-if="file.type === 'image'" class="image-preview">
          <img :src="file.url" :alt="file.name" />
          <div class="remove-btn" @click="handleFileRemove(file)">
            <el-icon><Close /></el-icon>
          </div>
        </div>
        <!-- 文件预览 -->
        <div v-else class="file-preview">
          <el-icon><Document /></el-icon>
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ (file.size / 1024).toFixed(1) }}KB</span>
          <div class="remove-btn" @click="handleFileRemove(file)">
            <el-icon><Close /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <el-input
      v-model="inputValue"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 6 }"
      placeholder="输入消息，Enter 发送，Shift + Enter 换行"
      resize="none"
      @keydown.enter.exact.prevent="handleSend"
      @keydown.enter.shift="handleNewline"
    />
    <div class="button-group">
      <el-upload
        class="upload-btn"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileUpload"
        accept=".pdf,.doc,.docx,.txt"
      >
        <button class="action-btn">
          <img src="@/assets/photo/附件.png" alt="link" />
        </button>
      </el-upload>
      <el-upload
        class="upload-btn"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileUpload"
        accept="image/*"
      >
        <button class="action-btn">
          <img src="@/assets/photo/图片.png" alt="picture" />
        </button>
      </el-upload>
      <div class="divider"></div>
      <!-- 暂停按钮：AI 生成中显示 -->
      <button v-if="props.loading" class="action-btn stop-btn" @click="handleStop" title="停止生成">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
      </button>
      <!-- 发送按钮：非生成中显示 -->
      <button
        v-else
        class="action-btn send-btn"
        :disabled="props.loading || isParsing"
        @click="handleSend"
      >
        <img src="@/assets/photo/发送.png" alt="send" />
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-input-wrapper {
  padding: 0.8rem;
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  .preview-area {
    margin-bottom: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .preview-item {
      position: relative;
      border-radius: 8px;
      overflow: hidden;

      .image-preview {
        width: 60px;
        height: 60px;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .file-preview {
        padding: 8px;
        background-color: #f4f4f5;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 8px;

        .file-name {
          max-width: 120px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .file-size {
          color: #909399;
          font-size: 12px;
        }
      }

      .remove-btn {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 20px;
        height: 20px;
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: white;

        &:hover {
          background-color: rgba(0, 0, 0, 0.7);
        }
      }
    }
  }

  :deep(.el-textarea__inner) {
    border-radius: 8px;
    resize: none;
    border: none;
    box-shadow: none;

    &:focus {
      border: none;
      box-shadow: none;
    }
  }

  .button-group {
    display: flex;
    justify-content: flex-end;
    margin-top: 0.25rem;
    gap: 0.5rem;
    align-items: center;

    .upload-btn {
      display: inline-block;
    }

    .divider {
      height: 1rem;
      width: 1px;
      background-color: var(--border-color);
      margin: 0;
      margin-left: 0.125rem;
      margin-right: 0.25rem;
    }

    .action-btn {
      width: 1.75rem;
      height: 1.75rem;
      border: none;
      background: none;
      padding: 0;
      cursor: pointer;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.3s;

      img {
        width: 1rem;
        height: 1rem;
      }

      &:hover {
        background-color: rgba(0, 0, 0, 0.05);
      }

      &.send-btn {
        width: 2rem;
        height: 2rem;
        background-color: #3f7af1;

        img {
          width: 1.25rem;
          height: 1.25rem;
        }

        &:hover {
          background-color: #3266d6;
        }

        &:disabled {
          background-color: #ccc;
          cursor: not-allowed;
        }
      }

      &.stop-btn {
        width: 2rem;
        height: 2rem;
        background-color: #ef4444;
        color: white;

        svg {
          width: 1rem;
          height: 1rem;
        }

        &:hover {
          background-color: #dc2626;
        }
      }
    }
  }
}
</style>