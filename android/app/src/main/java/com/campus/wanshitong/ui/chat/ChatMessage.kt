package com.campus.wanshitong.ui.chat

import android.net.Uri
import com.campus.wanshitong.data.model.AgentReply

/** 聊天界面消息模型。 */
sealed interface ChatMessage {
    val id: String

    /** 用户消息：文字与/或截图。 */
    data class User(
        override val id: String,
        val text: String = "",
        val imageUri: Uri? = null,
    ) : ChatMessage

    /** 智能体回复。 */
    data class Agent(
        override val id: String,
        val reply: AgentReply,
    ) : ChatMessage

    /** 系统提示（如网络异常）。 */
    data class Notice(
        override val id: String,
        val text: String,
    ) : ChatMessage
}
