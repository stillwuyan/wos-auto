package com.example.wosauto

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.graphics.Bitmap
import android.hardware.display.DisplayManager
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.view.WindowManager

class ScreenCaptureService : Service() {
    private lateinit var mediaProjection: MediaProjection
    private lateinit var imageReader: ImageReader
    private lateinit var virtualDisplay: android.hardware.display.VirtualDisplay
    private lateinit var mjpegServer: MjpegServer

    private var screenRatio: Int = 1
    private var lastFrameTime: Long = 0
    private var frameInterval: Int = 100

    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        mjpegServer = MjpegServer(8080)
        mjpegServer.start()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(1, notification)

        if (intent != null) {
            val resultCode = intent.getIntExtra("result_code", -1)
            val data = intent.getParcelableExtra<Intent>("data", Intent::class.java)
            val flag = intent.getBooleanExtra("jpeg", false)
            screenRatio = intent.getIntExtra("ratio", 1)
            frameInterval = intent.getIntExtra("interval", 100)

            mjpegServer.updateJpeg(flag)
            mjpegServer.updateInterval(frameInterval)

            if (resultCode == -1 && data != null) {
                val projectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
                mediaProjection = projectionManager.getMediaProjection(resultCode, data)
                setupVirtualDisplay()
            }
        }

        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                "screen_capture",
                "Screen Capture",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        return if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            Notification.Builder(this, "screen_capture")
                .setContentTitle("Screen Capture Active")
                .setContentText("Streaming screen as MJPEG")
                .setSmallIcon(R.drawable.ic_launcher_foreground)
                .build()
        } else {
            Notification.Builder(this)
                .setContentTitle("Screen Capture Active")
                .setContentText("Streaming screen as MJPEG")
                .setSmallIcon(R.drawable.ic_launcher_foreground)
                .build()
        }
    }

    private fun setupVirtualDisplay() {
        val windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        val metrics = windowManager.currentWindowMetrics
        val width = metrics.bounds.width() / screenRatio
        val height = metrics.bounds.height() / screenRatio
        val density = resources.configuration.densityDpi

        imageReader = ImageReader.newInstance(
            width, height,
            android.graphics.PixelFormat.RGBA_8888, 2
        )

        imageReader.setOnImageAvailableListener({ reader ->
            val image = reader.acquireLatestImage()
            if (image != null) {
                val now = System.currentTimeMillis()
                if (now - lastFrameTime >= frameInterval) {
                    val bitmap = imageToBitmap(image)
                    mjpegServer.updateFrame(bitmap)
                    lastFrameTime = now
                }
                image.close()
            }

        }, handler)

        virtualDisplay = mediaProjection.createVirtualDisplay(
            "ScreenCapture",
            width, height, density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader.surface, null, null
        )
    }

    private fun imageToBitmap(image: Image): Bitmap {
        val planes = image.planes
        val buffer = planes[0].buffer
        val width = image.width
        val height = image.height
        val pixelStride = planes[0].pixelStride
        val rowStride = planes[0].rowStride
        val rowPadding = rowStride - pixelStride * width

        mjpegServer.updatePadding(rowPadding / pixelStride)

        val bitmap = Bitmap.createBitmap(
            width + rowPadding / pixelStride,
            height,
            Bitmap.Config.ARGB_8888
        )
        bitmap.copyPixelsFromBuffer(buffer)
        return bitmap
    }

    override fun onDestroy() {
        super.onDestroy()
        mjpegServer.stop()
        virtualDisplay.release()
        mediaProjection.stop()
        imageReader.close()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}