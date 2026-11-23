package com.grupo8_uniandes.solventa

import android.app.Application
import com.grupo8_uniandes.solventa.di.startSolventaKoin
import com.grupo8_uniandes.solventa.push.PushNotificationBuilder
import com.grupo8_uniandes.solventa.push.logRegistration

class SolventaApp : Application() {
    override fun onCreate() {
        super.onCreate()
        startSolventaKoin(this)
        PushNotificationBuilder.ensureChannel(this)
        logRegistration(this)
    }
}
