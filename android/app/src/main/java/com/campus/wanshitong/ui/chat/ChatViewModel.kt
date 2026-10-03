package com.campus.wanshitong.ui.chat

import android.app.Application
import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.campus.wanshitong.data.local.AppPrefs
import com.campus.wanshitong.data.model.AgentReply
import com.campus.wanshitong.data.remote.ApiClient
import com.campus.wanshitong.data.repository.ChatRepository
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** 聊天界面状态与业务编排。 */
class ChatViewModel(
    private val app: Application,
    private val repository: ChatRepository,
    private val prefs: AppPrefs,
) : ViewModel() {

    var messages by mutableStateOf<List<ChatMessage>>(emptyList())
        private set

    var input by mutableStateOf("")
        private set

    var sending by mutableStateOf(false)
        private set

    var pendingImage by mutableStateOf<Uri?>(null)
        private set

    init {
        messages = listOf(
            ChatMessage.Agent(
                id = UUID.randomUUID().toString(),
                reply = AgentReply.Text("在。想问什么？可直接输入问题，或上传群里的通知截图。"),
            )
        )
    }

    fun onInputChange(value: String) {
        input = value
    }

    fun attachImage(uri: Uri?) {
        pendingImage = uri
    }

    fun send() {
        val text = input.trim()
        val image = pendingImage
        if (sending || (text.isEmpty() && image == null)) return

        messages = messages + ChatMessage.User(
            id = UUID.randomUUID().toString(),
            text = text,
            imageUri = image,
        )
        input = ""
        pendingImage = null
        sending = true

        viewModelScope.launch {
            runCatching { requestReply(text, image) }
                .onSuccess { reply ->
                    messages = messages + ChatMessage.Agent(UUID.randomUUID().toString(), reply)
                }
                .onFailure { error ->
                    messages = messages + ChatMessage.Notice(
                        id = UUID.randomUUID().toString(),
                        text = "网络异常，请稍后重试（${error.message ?: "未知错误"}）",
                    )
                }
            sending = false
        }
    }

    fun sendFeedback(messageId: String, useful: Boolean) {
        viewModelScope.launch {
            runCatching { repository.sendFeedback(messageId, useful) }
        }
    }

    private suspend fun requestReply(text: String, image: Uri?): AgentReply {
        val sessionId = prefs.sessionId()
        if (image == null) return repository.ask(sessionId, text)

        val bytes = withContext(Dispatchers.IO) {
            app.contentResolver.openInputStream(image)?.use { it.readBytes() }
        } ?: error("无法读取所选图片")
        return repository.askWithImage(sessionId, text, bytes)
    }

    companion object {
        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                val app = this[ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY] as Application
                ChatViewModel(
                    app = app,
                    repository = ChatRepository(ApiClient.api, ApiClient.gsonInstance),
                    prefs = AppPrefs(app),
                )
            }
        }
    }
}
