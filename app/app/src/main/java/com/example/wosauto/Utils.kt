package com.example.wosauto

import android.content.Context
import android.net.wifi.WifiManager
import java.math.BigInteger
import java.net.InetAddress
import java.nio.ByteOrder

fun Context.getLocalIpAddress(): String {
    val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    var ipAddress = wifiManager.connectionInfo.ipAddress

    // Convert little-endian to big-endian if needed
    if (ByteOrder.nativeOrder() == ByteOrder.LITTLE_ENDIAN) {
        ipAddress = Integer.reverseBytes(ipAddress)
    }

    val ipByteArray = BigInteger.valueOf(ipAddress.toLong()).toByteArray()
    return try {
        InetAddress.getByAddress(ipByteArray).hostAddress ?: "Unknown"
    } catch (e: Exception) {
        "Unknown"
    }
}