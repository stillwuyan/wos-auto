package com.example.wosauto

import android.content.Context
import android.os.Bundle
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import android.media.projection.MediaProjectionManager
import android.widget.TextView
import android.widget.Button
import android.content.Intent
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.CheckBox
import android.widget.Spinner
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import com.google.android.material.slider.Slider

class MainActivity : AppCompatActivity() {
    private companion object {
        private const val REQUEST_CODE_SCREEN_CAPTURE = 1001
    }

    private lateinit var projectionManager: MediaProjectionManager

    private lateinit var screenCaptureLauncher: ActivityResultLauncher<Intent>
    private var runningFlag: Boolean = false
    private var screenRatio: Int = 1
    private var frameInterval: Int = 100
    private var useJpg: Boolean = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

        val sliderInterval = findViewById<Slider>(R.id.slider_interval)
        val sliderText = findViewById<TextView>(R.id.text_interval)
        sliderInterval.addOnChangeListener { _, value, _ ->
            sliderText.text = "   Interval: ${value.toInt()}"
            frameInterval = value.toInt()
        }

        val ratioSpinner: Spinner = findViewById(R.id.screen_ratio)
        val numbers = arrayOf("1", "2", "4")
        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_item,
            numbers
        )
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        ratioSpinner.adapter = adapter
        ratioSpinner.setSelection(0)
        ratioSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: android.view.View?, position: Int, id: Long) {
                screenRatio = parent?.getItemAtPosition(position).toString().toInt(10)
            }
            override fun onNothingSelected(parent: AdapterView<*>?) {}
        }

        val typeCheckBox = findViewById<CheckBox>(R.id.type_jpeg)
        typeCheckBox.setOnCheckedChangeListener { _, isChecked ->
            useJpg = isChecked
        }

        projectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager

        screenCaptureLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult())
        { result ->
            if (result.resultCode == RESULT_OK && result.data != null) {
                startCaptureService(result.resultCode, result.data!!)
                moveTaskToBack(true)
            }
        }

        val startButton = findViewById<Button>(R.id.start_button)

        startButton.setOnClickListener {
            if (runningFlag) {
                stopCaptureService()
                startButton.text = "Start"
                runningFlag = false
            } else {
                requestScreenCapture()
                startButton.text = "Stop"
                runningFlag = true
            }
        }
    }

    private fun requestScreenCapture() {
        val captureIntent = projectionManager.createScreenCaptureIntent()
        screenCaptureLauncher.launch(captureIntent)
    }

    private fun startCaptureService(resultCode: Int, data: Intent) {
        val serviceIntent = Intent(this, ScreenCaptureService::class.java).apply {
            putExtra("result_code", resultCode)
            putExtra("data", data)
            putExtra("jpeg", useJpg)
            putExtra("ratio", screenRatio)
            putExtra("interval", frameInterval)
        }

        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun stopCaptureService() {
        val context: Context = this
        val serviceIntent = Intent(context, ScreenCaptureService::class.java)
        context.stopService(serviceIntent)
    }
}