package com.grupo8_uniandes.solventa

import android.app.Application
import com.grupo8_uniandes.solventa.di.startSolventaKoin

class SolventaApp : Application() {
    override fun onCreate() {
        super.onCreate()
        startSolventaKoin(this)
    }
}
