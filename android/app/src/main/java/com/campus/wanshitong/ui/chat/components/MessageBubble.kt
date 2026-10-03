package com.campus.wanshitong.ui.chat.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.campus.wanshitong.data.model.AgentReply
import com.campus.wanshitong.ui.chat.ChatMessage

/** 按消息类型渲染气泡 / 卡片。 */
@Composable
fun MessageBubble(message: ChatMessage, onFeedback: (String, Boolean) -> Unit) {
    when (message) {
        is ChatMessage.User -> UserBubble(message)
        is ChatMessage.Agent -> AgentBubble(message, onFeedback)
        is ChatMessage.Notice -> NoticeBubble(message)
    }
}

@Composable
private fun UserBubble(message: ChatMessage.User) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.End,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.primary)
                .padding(12.dp),
            horizontalAlignment = Alignment.End,
        ) {
            message.imageUri?.let { uri ->
                AsyncImage(
                    model = uri,
                    contentDescription = null,
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .sizeIn(maxWidth = 220.dp, maxHeight = 260.dp)
                        .clip(RoundedCornerShape(8.dp)),
                )
            }
            if (message.text.isNotBlank()) {
                Text(text = message.text, color = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}

@Composable
private fun AgentBubble(message: ChatMessage.Agent, onFeedback: (String, Boolean) -> Unit) {
    when (val reply = message.reply) {
        is AgentReply.Card -> Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Start,
        ) {
            Box(modifier = Modifier.widthIn(max = 340.dp)) {
                ActionCardView(card = reply.card) { useful -> onFeedback(message.id, useful) }
            }
        }

        is AgentReply.Refusal -> BubbleBox {
            Text(
                text = "很抱歉，${reply.refusal.message}",
                style = MaterialTheme.typography.bodyLarge,
            )
            if (reply.refusal.contact.isNotBlank()) {
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "咨询渠道：${reply.refusal.contact}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        is AgentReply.Text -> BubbleBox {
            Text(text = reply.text, style = MaterialTheme.typography.bodyLarge)
        }
    }
}

@Composable
private fun BubbleBox(content: @Composable ColumnScope.() -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.Start,
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.surface)
                .padding(12.dp),
            content = content,
        )
    }
}

@Composable
private fun NoticeBubble(message: ChatMessage.Notice) {
    Box(
        modifier = Modifier.fillMaxWidth(),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = message.text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
