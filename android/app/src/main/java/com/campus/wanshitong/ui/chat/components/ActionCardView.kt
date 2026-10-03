package com.campus.wanshitong.ui.chat.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Checkbox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.campus.wanshitong.data.api.dto.ActionCardDto
import com.campus.wanshitong.data.api.dto.MaterialDto
import com.campus.wanshitong.ui.theme.Warning

/**
 * 结构化办事卡片（设计文档 附录D）。
 * 材料清单可勾选；字段缺失时按后端兜底文案展示。
 */
@Composable
fun ActionCardView(card: ActionCardDto, onFeedback: (Boolean) -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.primaryContainer, RoundedCornerShape(12.dp))
            .padding(16.dp),
    ) {
        Text(
            text = "📋 ${card.matterName}",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
        )

        if (card.targetUsers.isNotEmpty()) {
            Spacer(Modifier.height(4.dp))
            Text(
                text = "适用对象：" + card.targetUsers.joinToString("、"),
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        if (card.materials.isNotEmpty()) {
            Spacer(Modifier.height(12.dp))
            Text("✅ 所需材料", fontWeight = FontWeight.SemiBold, style = MaterialTheme.typography.bodyMedium)
            card.materials.forEach { material -> MaterialRow(material) }
        }

        Spacer(Modifier.height(12.dp))
        HorizontalDivider()
        Spacer(Modifier.height(12.dp))

        InfoLine("📍", "办理地点", card.location)
        InfoLine("🕐", "办公时间", card.officeHours)
        InfoLine("⏰", "截止日期", card.deadline ?: "未查到明确期限", highlight = card.deadline != null)
        InfoLine("🧭", "办理方式", card.channel)
        InfoLine("☎️", "咨询渠道", card.contact.ifBlank { "未查到" })

        if (card.sources.isNotEmpty()) {
            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(8.dp))
            card.sources.forEach { source ->
                Text(
                    text = "📎 出处：《${source.title}》${source.issuer} ${source.date.orEmpty()}".trim(),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        card.notes.forEach { note ->
            Spacer(Modifier.height(4.dp))
            Text("💡 $note", style = MaterialTheme.typography.bodySmall)
        }

        if (card.confidence <= 0.6) {
            Spacer(Modifier.height(6.dp))
            Text(
                text = "⚠️ 信息可能不完整，建议向相关部门确认",
                style = MaterialTheme.typography.bodySmall,
                color = Warning,
            )
        }

        Spacer(Modifier.height(4.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("这条回答：", style = MaterialTheme.typography.bodySmall)
            TextButton(onClick = { onFeedback(true) }) { Text("有用") }
            TextButton(onClick = { onFeedback(false) }) { Text("没用") }
        }
    }
}

@Composable
private fun MaterialRow(material: MaterialDto) {
    var checked by remember { mutableStateOf(false) }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { checked = !checked },
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Checkbox(checked = checked, onCheckedChange = { checked = it })
        Text(
            text = material.item + if (material.note.isNullOrBlank()) "" else "（${material.note}）",
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun InfoLine(icon: String, label: String, value: String, highlight: Boolean = false) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.Start,
    ) {
        Text("$icon ", style = MaterialTheme.typography.bodyMedium)
        Text(
            text = "$label：",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = if (highlight) FontWeight.Bold else FontWeight.Normal,
            color = if (highlight) Warning else MaterialTheme.colorScheme.onSurface,
        )
    }
}
