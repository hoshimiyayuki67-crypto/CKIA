package com.campus.wanshitong

import android.app.Application

/**
 * 应用入口 Application。
 *
 * 网络客户端在 ApiClient 中以单例持有，此处保留扩展位
 * （后续可接入依赖注入、崩溃上报、全局配置等）。
 */
class CampusApplication : Application()
