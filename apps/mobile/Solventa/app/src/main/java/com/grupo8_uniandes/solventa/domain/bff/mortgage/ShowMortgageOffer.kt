package com.grupo8_uniandes.solventa.domain.bff.mortgage

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import java.math.BigDecimal

data class FirmMortgageOffer(
    val title: String,
    val heading: String,
    val coverage: String,
    val prima: Long,
    val moneda: String,
    val amountText: String,
    val premiumText: String,
)

class ShowMortgageOffer(
    private val region: Region = Region.Colombia,
) {
    fun show(
        coverage: String = DEFAULT_COVERAGE,
        prima: Long = DEFAULT_PRIMA,
        moneda: String = DEFAULT_MONEDA,
    ): FirmMortgageOffer {
        val amountText = formatPremium(BigDecimal(prima), moneda, region)
        return FirmMortgageOffer(
            title = TITLE,
            heading = HEADING,
            coverage = coverage,
            prima = prima,
            moneda = moneda,
            amountText = amountText,
            premiumText = amountText + PER_MONTH,
        )
    }

    companion object {
        const val TITLE = "Vida hipotecario · paso 2 de 3"
        const val HEADING = "Vida hipotecario · oferta en firme"
        const val DEFAULT_COVERAGE = "Protección de pagos · prima según tu perfil"
        const val DEFAULT_PRIMA = 89_500L
        const val DEFAULT_MONEDA = "COP"
        const val PER_MONTH = " / mes"
    }
}
