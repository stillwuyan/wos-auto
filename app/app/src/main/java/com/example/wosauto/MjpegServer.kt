package com.example.wosauto

import android.graphics.Bitmap
import android.util.Log
import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.io.IOException
import java.io.OutputStream
import java.net.ServerSocket
import java.net.Socket
import java.nio.ByteBuffer
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MjpegServer(private val port: Int) {
    private companion object {
        private const val BOUNDARY = "MjpegFrame"
        private val HEADER = """
            HTTP/1.0 200 OK
            Server: Android MJPEG Server
            Connection: close
            Max-Age: 0
            Expires: 0
            Cache-Control: no-cache, private
            Pragma: no-cache
            Content-Type: multipart/x-mixed-replace; boundary=$BOUNDARY
            
            --$BOUNDARY
            
        """.trimIndent().replace("\n", "\r\n")

        private val FRAME_HEADER = """
            Content-Type: image/jpeg
            Content-Length: %d
            
        """.trimIndent().replace("\n", "\r\n")
    }

    @Volatile
    private var isRunning = false
    private var serverSocket: ServerSocket? = null
    private val executor: ExecutorService = Executors.newCachedThreadPool()
    @Volatile
    private var currentFrame: Bitmap? = null

    @Volatile
    private var paddingSaved: Int = 0

    private var useJpeg: Boolean = false
    private var frameInterval: Int = 100

    private val reusableBuffer = ThreadLocal<ByteBuffer>()

    fun start() {
        if (isRunning) return

        isRunning = true
        executor.execute(this::runServer)
    }

    fun stop() {
        isRunning = false
        try {
            serverSocket?.close()
        } catch (e: IOException) {
            Log.e("MjpegServer", "Error closing server", e)
        }
        executor.shutdown()
    }

    fun updateFrame(frame: Bitmap) {
        currentFrame = frame
    }

    fun updatePadding(padding: Int) {
        if (padding != paddingSaved) {
            paddingSaved = padding
        }
    }

    fun updateJpeg(flag: Boolean) {
        useJpeg = flag
    }

    fun updateInterval(interval: Int) {
        frameInterval = interval
    }

    private fun runServer() {
        try {
            serverSocket = ServerSocket(port)
            serverSocket?.reuseAddress = true

            while (isRunning) {
                try {
                    val client = serverSocket?.accept()
                    if (client != null) {
                        executor.execute { handleClient(client) }
                    }
                } catch (e: IOException) {
                    if (isRunning) {
                        Log.e("MjpegServer", "Client connection error", e)
                    }
                }
            }
        } catch (e: IOException) {
            Log.e("MjpegServer", "Server error", e)
        }
    }

    private fun outputRgba(frame: Bitmap, output: OutputStream) {
        val width = frame.width
        val height = frame.height
        val pixelCount = width * height
        val rgbaSize = pixelCount * 4
        val totalSize = 16 + rgbaSize

        val frameHeader = String.format(FRAME_HEADER, totalSize)
        output.write(frameHeader.toByteArray())

        val buffer = reusableBuffer.get()?.takeIf { it.capacity() >= totalSize }
            ?: ByteBuffer.allocate(totalSize).also { reusableBuffer.set(it) }
        buffer.clear()

        buffer.putInt(width).putInt(height).putInt(paddingSaved).putInt(rgbaSize)
        frame.copyPixelsToBuffer(buffer)

        output.write(buffer.array(), 0, buffer.position())
    }

    private fun outputJpeg(frame: Bitmap, frameStream: ByteArrayOutputStream, output: OutputStream) {
        frameStream.reset()
        frame.compress(Bitmap.CompressFormat.JPEG, 70, frameStream)

        val frameBytes = frameStream.toByteArray()
        val frameHeader = String.format(FRAME_HEADER, frameBytes.size)
        output.write(frameHeader.toByteArray())
        output.write(frameBytes)
        return
    }

    private fun handleClient(client: Socket) {
        var output: OutputStream? = null
        try {
            output = client.getOutputStream()
            output.write(HEADER.toByteArray())

            val frameStream = ByteArrayOutputStream()

            while (isRunning && !client.isClosed) {
                val frame = currentFrame
                if (frame == null) {
                    Thread.sleep((frameInterval / 3).toLong())
                    continue
                }

                if (useJpeg) {
                    outputJpeg(frame, frameStream, output)
                } else {
                    outputRgba(frame, output)
                }

                output.write("\r\n--$BOUNDARY\r\n".toByteArray())
                output.flush()

                // Control frame rate (e.g. 15 FPS)
                Thread.sleep(frameInterval.toLong())
            }
        } catch (e: Exception) {
            Log.e("MjpegServer", "Client handling error", e)
        } finally {
            try {
                output?.close()
                client.close()
            } catch (e: IOException) {
                Log.e("MjpegServer", "Error closing client", e)
            }
        }
    }
}