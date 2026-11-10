package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeDestination
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeEntry
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeKind

data class ParametricNotice(
    val asunto: String,
    val disparo: String,
    val monto: Long,
    val moneda: String,
    val lineaDepositada: String,
)

data class ParametricReceipt(
    val asunto: String,
    val disparo: String,
    val lineaDepositada: String,
)

class OpenParametricPayment(
    private val claims: ClaimRepository,
) {
    suspend fun open(claimId: String): ParametricNotice? {
        val listed = claims.list() as? StandInAnswer.Ready ?: return null
        val stored = listed.value.find { it.siniestroId == claimId } ?: return null
        if (!stored.isParametricPayment()) return null
        return review
    }

    fun open(push: NoticeEntry): ParametricNotice? = if (opens(push)) review else null

    fun receipt(notice: ParametricNotice) = ParametricReceipt(
        asunto = notice.asunto,
        disparo = notice.disparo,
        lineaDepositada = notice.lineaDepositada,
    )

    private fun ClaimSummary.isParametricPayment(): Boolean =
        estado == ClaimStatus.PAGADO && estadoTexto == STORED_STATUS

    companion object {
        const val STORED_ID = "SIN-P01"
        const val STORED_STATUS = "Pago automático · pagado"
        const val HEADING = "Pago automático realizado"
        const val SUBJECT = "Clima y vuelos · vuelo AV-234"
        const val TRIGGER = "Retraso > 90 min · dato oficial del vuelo"
        const val AMOUNT = 180_000L
        const val CURRENCY = "COP"
        const val DEPOSITED = "$180.000 COP depositados"
        const val POLICY = "POL-77310"

        val review = ParametricNotice(
            asunto = SUBJECT,
            disparo = TRIGGER,
            monto = AMOUNT,
            moneda = CURRENCY,
            lineaDepositada = DEPOSITED,
        )

        fun reviewPush(poliza: String = "POL-88219-CO") = NoticeEntry(
            tipo = NoticeKind.PAGO_AUTOMATICO,
            titulo = HEADING,
            cuerpo = TRIGGER,
            destino = NoticeDestination.PARAMETRICO,
            poliza = poliza,
        )

        fun opens(push: NoticeEntry): Boolean =
            push.tipo == NoticeKind.PAGO_AUTOMATICO &&
                push.destino == NoticeDestination.PARAMETRICO &&
                push.titulo == HEADING &&
                push.cuerpo == TRIGGER
    }
}
