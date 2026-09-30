package com.arcanaforensics.arcalume

import android.app.Application
import android.util.Log
import com.arcanaforensics.arcalume.data.ProStore
import com.arcanaforensics.arcalume.data.createProStore
import org.opencv.android.OpenCVLoader

class ArcalumeApp : Application() {
    lateinit var pro: ProStore
        private set

    override fun onCreate() {
        super.onCreate()
        if (!OpenCVLoader.initLocal()) Log.e("Arcalume", "OpenCV native library failed to load")
        pro = createProStore(this)
    }
}
