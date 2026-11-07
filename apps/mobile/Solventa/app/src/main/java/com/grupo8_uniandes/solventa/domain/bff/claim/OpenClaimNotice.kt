package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import java.time.LocalDate
import java.util.UUID

enum class NoticePhase {
    Form,
    Evidence,
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
    val geotag: Boolean = false,
    val cameraDenied: Boolean = false,
) {
    fun toNotice() = ClaimNotice(
        poliza = poliza,
        fechaHecho = fechaHecho,
        geo = geo,
        adjuntos = adjuntos,
        descripcion = descripcion.trim(),
        lugar = lugar.trim(),
    )

    fun displaySentences() = listOf(
        "$poliza · Protección de dispositivo",
        "12 mar 2026",
        descripcion,
        lugar,
    )

    fun helpLines() = listOf(
        "Los campos siguen el ramo de la póliza que elijas",
        "Escribe el lugar. Geoetiqueta solo si la activas.",
    )

    companion object {
        val Empty = ClaimNoticeDraft(
            poliza = "",
            fechaHecho = "",
            descripcion = "",
            lugar = "",
            geo = null,
            locationDenied = false,
            adjuntos = emptyList(),
        )

        val Review = ClaimNoticeDraft(
            poliza = "POL-88219-CO",
            fechaHecho = "2026-03-12",
            descripcion = "Pantalla rota al caer el teléfono",
            lugar = "Av. Caracas con Calle 72",
            geo = null,
            locationDenied = false,
            adjuntos = emptyList(),
        )

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
    private val archive: NoticeArchive? = null,
    private val today: () -> LocalDate = { LocalDate.now() },
    private val newKey: () -> String = { UUID.randomUUID().toString() },
) {
    var phase: NoticePhase = NoticePhase.Form
        private set

    var draft: ClaimNoticeDraft = ClaimNoticeDraft.Empty
        private set

    var receipt: ClaimReceipt? = null
        private set

    var attempted: Boolean = false
        private set

    var rejection: String? = null
        private set

    var sending: Boolean = false
        private set

    var queued: Boolean = false
        private set

    private var offered: List<String> = emptyList()

    fun review(): ClaimNoticeDraft = draft

    fun offerPolicies(numbers: List<String>) {
        offered = numbers
        draft = when {
            numbers.size == 1 -> draft.copy(poliza = numbers.single())
            draft.poliza !in numbers -> draft.copy(poliza = "")
            else -> draft
        }
    }

    fun revise(
        poliza: String = draft.poliza,
        fechaHecho: String = draft.fechaHecho,
        descripcion: String = draft.descripcion,
        lugar: String = draft.lugar,
    ) {
        draft = draft.copy(
            poliza = poliza,
            fechaHecho = fechaHecho,
            descripcion = descripcion,
            lugar = lugar,
        )
    }

    fun problems(): NoticeProblems = draft.problems(today(), offered, attempted)

    fun sendOffered(): Boolean = phase == NoticePhase.Evidence

    fun continueToEvidence() {
        attempted = true
        if (!draft.problems(today(), offered, attempted = true).canContinue) return
        phase = NoticePhase.Evidence
    }

    fun setGeotag(on: Boolean) {
        draft = if (on) {
            draft.copy(geotag = true)
        } else {
            draft.copy(geotag = false, geo = null, locationDenied = false)
        }
    }

    fun placeAt(geo: GeoPoint?) {
        draft = if (geo == null) {
            draft.copy(geo = null, locationDenied = true)
        } else {
            draft.copy(geo = geo, geotag = true, locationDenied = false)
        }
    }

    fun markCameraDenied() {
        draft = draft.copy(cameraDenied = true)
    }

    fun attachFile(attachment: Attachment, bytes: ByteArray? = null): Boolean {
        if (!attachment.accepted()) return false
        if (draft.adjuntos.size >= 5) return false
        if (bytes != null) EvidenceBytes.keep(attachment.nombre, bytes)
        draft = draft.copy(adjuntos = draft.adjuntos + attachment)
        return true
    }

    fun remove(nombre: String) {
        EvidenceBytes.drop(nombre)
        draft = draft.copy(adjuntos = draft.adjuntos.filterNot { it.nombre == nombre })
    }

    fun queue(): String {
        val notice = draft.toNotice()
        val key = hold.readKey() ?: newKey()
        hold.keep(key, notice)
        archive?.keep(key, notice, notice.storedFiles())
        queued = true
        return key
    }

    suspend fun send(): ClaimReceipt? {
        receipt?.let { return it }
        if (sending || draft.adjuntos.isEmpty()) return null
        sending = true
        val key = hold.readKey() ?: newKey().also { hold.keep(it, draft.toNotice()) }
        return try {
            when (val answer = claims.notify(draft.toNotice(), key)) {
                is StandInAnswer.Ready -> answer.value.also {
                    receipt = it
                    rejection = null
                    queued = false
                    phase = NoticePhase.Confirmation
                    hold.clear()
                    archive?.clear()
                }
                is StandInAnswer.Rejected -> {
                    rejection = answer.message
                    queued = false
                    hold.clear()
                    archive?.clear()
                    null
                }
                else -> {
                    val notice = draft.toNotice()
                    archive?.keep(key, notice, notice.storedFiles())
                    null
                }
            }
        } finally {
            sending = false
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
            draft = ClaimNoticeDraft.Empty
            receipt = null
        }
    }
}

data class NoticeProblems(
    val policy: Boolean = false,
    val date: Boolean = false,
    val description: Boolean = false,
    val place: Boolean = false,
    val noPolicy: Boolean = false,
) {
    val canContinue: Boolean get() = !policy && !date && !description && !place && !noPolicy
}

private val acceptedTypes = setOf("image/png", "image/jpeg", "application/pdf", "video/mp4")

fun Attachment.accepted(): Boolean {
    if (contentType == "application/octet-stream" && tamanoBytes == 0L) return true
    return contentType in acceptedTypes && tamanoBytes in 1..(10L * 1024 * 1024)
}

fun ClaimNoticeDraft.problems(
    today: java.time.LocalDate,
    offered: List<String>,
    attempted: Boolean,
): NoticeProblems {
    if (!attempted && offered.isNotEmpty()) {
        return NoticeProblems(noPolicy = offered.isEmpty())
    }
    if (offered.isEmpty() && poliza.isBlank()) return NoticeProblems(noPolicy = true)
    val date = runCatching { java.time.LocalDate.parse(fechaHecho) }.getOrNull()
    val description = descripcion.trim()
    return NoticeProblems(
        policy = poliza.isBlank() || (offered.isNotEmpty() && poliza !in offered),
        date = date == null || date.isAfter(today),
        description = description.isEmpty() || description.length > 1000,
        place = lugar.trim().length > 200,
        noPolicy = offered.isEmpty() && poliza.isBlank(),
    )
}

fun List<com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary>.filtered(
    chip: ClaimChip,
): List<com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary> = when (chip) {
    ClaimChip.Todos -> this
    ClaimChip.EnEvaluacion -> filter { it.estado == ClaimStatus.EN_EVALUACION }
    ClaimChip.Pagado -> filter { it.estado == ClaimStatus.PAGADO }
}

enum class ClaimChip { Todos, EnEvaluacion, Pagado }
