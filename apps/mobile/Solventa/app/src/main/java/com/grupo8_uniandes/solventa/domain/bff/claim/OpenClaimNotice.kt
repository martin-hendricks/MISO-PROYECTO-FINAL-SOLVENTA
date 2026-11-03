package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import java.util.UUID

enum class NoticePhase {
    Form,
    Camera,
    Photos,
    Evidence,
    Location,
    GeoDenied,
    CameraDenied,
    Confirmation,
    Closed,
}

data class ClaimNoticeDraft(
    val poliza: String,
    val fechaHecho: String,
    val descripcion: String,
    val lugar: String,
    val geo: GeoPoint?,
    val locationDenied: Boolean,
    val adjuntos: List<Attachment>,
) {
    fun toNotice() = ClaimNotice(
        poliza = poliza,
        fechaHecho = fechaHecho,
        geo = geo,
        adjuntos = adjuntos,
    )

    fun displaySentences() = listOf(
        "$poliza · Protección de dispositivo",
        "12 mar 2026",
        descripcion,
        lugar,
    )

    fun helpLines() = listOf(
        "Los campos siguen el ramo de la póliza que elijas",
        "Pide permiso de ubicacion del dispositivo para geoetiquetar",
    )

    companion object {
        val Review = ClaimNoticeDraft(
            poliza = "POL-88219-CO",
            fechaHecho = "2026-03-12",
            descripcion = "Pantalla rota al caer el teléfono",
            lugar = "Av. Caracas con Calle 72",
            geo = null,
            locationDenied = false,
            adjuntos = emptyList(),
        )

        val AllowedGeo = GeoPoint(lat = 4.6533, lng = -74.0836, precisionM = 12)

        fun photo() = Attachment(AttachmentKind.FOTO, "foto-dano")

        fun video() = Attachment(AttachmentKind.VIDEO, "video-dano")

        fun receiptFile() = Attachment(AttachmentKind.RECIBO, "recibo-dano")

        fun support() = Attachment(AttachmentKind.SOPORTE, "soporte-recorte")
    }
}

interface ClaimHold {
    fun keep(key: String, notice: ClaimNotice)

    fun readKey(): String?

    fun clear()
}

class MemoryClaimHold : ClaimHold {
    private var key: String? = null
    private var notice: ClaimNotice? = null

    override fun keep(key: String, notice: ClaimNotice) {
        this.key = key
        this.notice = notice
    }

    override fun readKey(): String? = key

    override fun clear() {
        key = null
        notice = null
    }

    fun readNotice(): ClaimNotice? = notice
}

class OpenClaimNotice(
    private val claims: ClaimRepository,
    private val hold: ClaimHold = MemoryClaimHold(),
    private val newKey: () -> String = { UUID.randomUUID().toString() },
) {
    var phase: NoticePhase = NoticePhase.Form
        private set

    var draft: ClaimNoticeDraft = ClaimNoticeDraft.Review
        private set

    var receipt: ClaimReceipt? = null
        private set

    fun review(): ClaimNoticeDraft = draft

    fun sendOffered(): Boolean = phase == NoticePhase.Evidence ||
        phase == NoticePhase.GeoDenied ||
        phase == NoticePhase.CameraDenied

    fun continueToCamera() {
        phase = NoticePhase.Camera
    }

    fun allowCamera() {
        draft = draft.plus(ClaimNoticeDraft.photo())
        phase = NoticePhase.Evidence
    }

    fun denyCamera() {
        phase = NoticePhase.CameraDenied
    }

    fun dismissCamera() {
        phase = NoticePhase.Evidence
    }

    fun choosePhotos() {
        phase = NoticePhase.Photos
    }

    fun allowPhotos() {
        draft = draft.plus(ClaimNoticeDraft.photo())
        phase = NoticePhase.Evidence
    }

    fun denyPhotos() {
        phase = NoticePhase.CameraDenied
    }

    fun attachVideo() {
        draft = draft.plus(ClaimNoticeDraft.video())
    }

    fun attachReceipt() {
        draft = draft.plus(ClaimNoticeDraft.receiptFile())
    }

    fun attachSupport() {
        draft = draft.plus(ClaimNoticeDraft.support())
    }

    fun openLocation() {
        phase = NoticePhase.Location
    }

    fun allowLocation() {
        draft = draft.copy(geo = ClaimNoticeDraft.AllowedGeo, locationDenied = false)
        phase = NoticePhase.Evidence
    }

    fun denyLocation() {
        draft = draft.copy(geo = null, locationDenied = true)
        phase = NoticePhase.GeoDenied
    }

    fun dismissLocation() {
        draft = draft.copy(geo = null)
        phase = NoticePhase.Evidence
    }

    fun queue(): String {
        val key = hold.readKey() ?: newKey()
        hold.keep(key, draft.toNotice())
        return key
    }

    suspend fun send(): ClaimReceipt? {
        receipt?.let { return it }
        val key = hold.readKey() ?: newKey().also { hold.keep(it, draft.toNotice()) }
        return when (val answer = claims.notify(draft.toNotice(), key)) {
            is StandInAnswer.Ready -> answer.value.also {
                receipt = it
                phase = NoticePhase.Confirmation
                hold.clear()
            }
            else -> null
        }
    }

    fun cancel() {
        hold.clear()
        receipt = null
        phase = NoticePhase.Closed
    }

    fun reopen() {
        if (phase == NoticePhase.Closed || phase == NoticePhase.Confirmation) {
            phase = NoticePhase.Form
            draft = ClaimNoticeDraft.Review
            receipt = null
        }
    }

    private fun ClaimNoticeDraft.plus(attachment: Attachment): ClaimNoticeDraft {
        if (adjuntos.any { it.tipo == attachment.tipo }) return this
        return copy(adjuntos = adjuntos + attachment)
    }
}
