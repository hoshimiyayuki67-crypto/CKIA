# 保留 Retrofit / Gson 相关签名
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.campus.wanshitong.data.api.dto.** { *; }
-keep class retrofit2.** { *; }
-dontwarn okhttp3.**
-dontwarn retrofit2.**
