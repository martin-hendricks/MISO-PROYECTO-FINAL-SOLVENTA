package com.grupo8_uniandes.solventa.navigation

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import com.grupo8_uniandes.solventa.R

enum class Destination(
    @param:StringRes val labelRes: Int,
    @param:DrawableRes val iconRes: Int,
    val order: Int,
) {
    Inicio(R.string.destination_inicio, R.drawable.home, 0),
    Polizas(R.string.destination_polizas, R.drawable.description, 1),
    Siniestros(R.string.destination_siniestros, R.drawable.emergency_home, 2),
    Perfil(R.string.destination_perfil, R.drawable.person, 3),
    ;

    fun rootRoute(): Any = when (this) {
        Inicio -> InicioRoute
        Polizas -> PolizasRoute
        Siniestros -> SiniestrosRoute
        Perfil -> PerfilRoute
    }
}
