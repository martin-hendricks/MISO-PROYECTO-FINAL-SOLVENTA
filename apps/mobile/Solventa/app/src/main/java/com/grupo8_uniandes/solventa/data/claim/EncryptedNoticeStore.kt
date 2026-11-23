package com.grupo8_uniandes.solventa.data.claim

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.util.Base64
import com.grupo8_uniandes.solventa.domain.bff.claim.Attachment
import com.grupo8_uniandes.solventa.domain.bff.claim.AttachmentKind
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.GeoPoint
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticeArchive
import org.json.JSONArray
import org.json.JSONObject
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

data class KeptNotice(val key: String, val notice: ClaimNotice, val files: List<ByteArray>)

class EncryptedNoticeStore(context: Context, passphrase: String) : NoticeArchive {
    private val secret = SecretKeySpec(passphrase.toByteArray().copyOf(16), "AES")
    private val db: SQLiteDatabase = context.openOrCreateDatabase("pending-notice", Context.MODE_PRIVATE, null).apply {
        execSQL(
            "CREATE TABLE IF NOT EXISTS pending (id INTEGER PRIMARY KEY, idempotency TEXT NOT NULL, payload BLOB NOT NULL)",
        )
    }

    override fun keep(key: String, notice: ClaimNotice, files: List<ByteArray>) {
        save(KeptNotice(key, notice, files))
    }

    fun save(kept: KeptNotice) {
        val payload = encrypt(kept.encode())
        db.execSQL("DELETE FROM pending")
        db.execSQL("INSERT INTO pending (idempotency, payload) VALUES (?, ?)", arrayOf(kept.key, payload))
    }

    fun read(): KeptNotice? {
        db.rawQuery("SELECT payload FROM pending LIMIT 1", null).use { cursor ->
            if (!cursor.moveToFirst()) return null
            return runCatching { decode(decrypt(cursor.getBlob(0))) }.getOrNull()
        }
    }

    override fun clear() {
        db.execSQL("DELETE FROM pending")
    }

    private fun encrypt(plain: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val nonce = ByteArray(12).also { SecureRandom().nextBytes(it) }
        cipher.init(Cipher.ENCRYPT_MODE, secret, GCMParameterSpec(128, nonce))
        return nonce + cipher.doFinal(plain)
    }

    private fun decrypt(blob: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, secret, GCMParameterSpec(128, blob.copyOf(12)))
        return cipher.doFinal(blob.copyOfRange(12, blob.size))
    }
}

private fun KeptNotice.encode(): ByteArray {
    val json = JSONObject()
    json.put("key", key)
    json.put("poliza", notice.poliza)
    json.put("fechaHecho", notice.fechaHecho)
    json.put("descripcion", notice.descripcion)
    json.put("lugar", notice.lugar)
    notice.geo?.let { geo ->
        json.put("lat", geo.lat)
        json.put("lng", geo.lng)
        json.put("precisionM", geo.precisionM)
    }
    val adjuntos = JSONArray()
    notice.adjuntos.forEach { file ->
        adjuntos.put(
            JSONObject()
                .put("tipo", file.tipo.name)
                .put("nombre", file.nombre)
                .put("contentType", file.contentType)
                .put("tamanoBytes", file.tamanoBytes),
        )
    }
    json.put("adjuntos", adjuntos)
    val blobs = JSONArray()
    files.forEach { blobs.put(Base64.encodeToString(it, Base64.NO_WRAP)) }
    json.put("files", blobs)
    return json.toString().toByteArray()
}

private fun decode(plain: ByteArray): KeptNotice {
    val json = JSONObject(String(plain))
    val geo = if (json.has("lat")) {
        GeoPoint(json.getDouble("lat"), json.getDouble("lng"), json.getInt("precisionM"))
    } else {
        null
    }
    val adjuntosJson = json.getJSONArray("adjuntos")
    val adjuntos = buildList {
        for (index in 0 until adjuntosJson.length()) {
            val file = adjuntosJson.getJSONObject(index)
            add(
                Attachment(
                    tipo = AttachmentKind.valueOf(file.getString("tipo")),
                    nombre = file.getString("nombre"),
                    contentType = file.getString("contentType"),
                    tamanoBytes = file.getLong("tamanoBytes"),
                ),
            )
        }
    }
    val blobs = json.getJSONArray("files")
    val files = buildList {
        for (index in 0 until blobs.length()) {
            add(Base64.decode(blobs.getString(index), Base64.NO_WRAP))
        }
    }
    return KeptNotice(
        key = json.getString("key"),
        notice = ClaimNotice(
            poliza = json.getString("poliza"),
            fechaHecho = json.getString("fechaHecho"),
            geo = geo,
            adjuntos = adjuntos,
            descripcion = json.optString("descripcion"),
            lugar = json.optString("lugar"),
        ),
        files = files,
    )
}
