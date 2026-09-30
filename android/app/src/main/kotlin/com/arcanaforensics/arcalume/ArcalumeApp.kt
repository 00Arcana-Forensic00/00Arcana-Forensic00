package com.arcanaforensics.arcalume

import android.app.Application
import android.util.Log
import com.arcanaforensics.arcalume.data.TrialProStore
import com.arcanaforensics.arcalume.data.createProStore
import org.opencv.android.OpenCVLoader

class ArcalumeApp : Application() {
    lateinit var pro: TrialProStore
        private set

    override fun onCreate() {
        super.onCreate()
        if (!OpenCVLoader.initLocal()) Log.e("Arcalume", "OpenCV native library failed to load")
        pro = TrialProStore(createProStore(this), getSharedPreferences("offer", MODE_PRIVATE))
    }
}
