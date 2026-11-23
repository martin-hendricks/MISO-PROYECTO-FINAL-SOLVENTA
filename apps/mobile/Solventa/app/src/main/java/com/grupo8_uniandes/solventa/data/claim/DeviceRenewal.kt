package com.grupo8_uniandes.solventa.data.claim

import android.content.Context
import com.grupo8_uniandes.solventa.domain.bff.claim.LocalRenewal

class DeviceRenewal(context: Context) : LocalRenewal {
    private val prefs = context.getSharedPreferences("parametric-renewal", Context.MODE_PRIVATE)

    override fun read(poliza: String): Boolean = prefs.getBoolean(poliza, false)

    override fun write(poliza: String, enabled: Boolean) {
        prefs.edit().putBoolean(poliza, enabled).apply()
    }
}
