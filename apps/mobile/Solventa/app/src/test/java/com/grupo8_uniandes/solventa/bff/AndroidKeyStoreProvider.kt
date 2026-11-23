package com.grupo8_uniandes.solventa.bff

import android.security.keystore.KeyGenParameterSpec
import java.security.Key
import java.security.KeyStore
import java.security.KeyStoreSpi
import java.security.Provider
import java.security.SecureRandom
import java.security.Security
import java.security.cert.Certificate
import java.security.spec.AlgorithmParameterSpec
import java.util.Collections
import java.util.Date
import java.util.concurrent.ConcurrentHashMap
import javax.crypto.KeyGeneratorSpi
import javax.crypto.SecretKey
import javax.crypto.spec.SecretKeySpec

/**
 * Robolectric 4.15 has no AndroidKeyStore. EncryptedSharedPreferences still asks for one.
 * This provider exists only in the JVM suite. The app uses the platform keystore.
 */
internal class AndroidKeyStoreProvider : Provider("AndroidKeyStore", 1.0, "JVM AndroidKeyStore") {
    init {
        put("KeyStore.AndroidKeyStore", FakeAndroidKeyStore::class.java.name)
        put("KeyGenerator.AES", FakeAndroidAesKeyGenerator::class.java.name)
    }

    companion object {
        fun install() {
            if (Security.getProvider("AndroidKeyStore") == null) {
                Security.insertProviderAt(AndroidKeyStoreProvider(), 1)
            }
        }
    }
}

internal object AndroidKeyStoreKeys {
    val keys: MutableMap<String, SecretKey> = ConcurrentHashMap()
}

internal class FakeAndroidKeyStore : KeyStoreSpi() {
    override fun engineGetKey(alias: String?, password: CharArray?): Key? = AndroidKeyStoreKeys.keys[alias]

    override fun engineGetCertificateChain(alias: String?): Array<Certificate>? = null

    override fun engineGetCertificate(alias: String?): Certificate? = null

    override fun engineGetCreationDate(alias: String?): Date? = Date(0)

    override fun engineSetKeyEntry(alias: String?, key: Key?, password: CharArray?, chain: Array<out Certificate>?) {
        if (alias != null && key is SecretKey) AndroidKeyStoreKeys.keys[alias] = key
    }

    override fun engineSetKeyEntry(alias: String?, key: ByteArray?, chain: Array<out Certificate>?) = Unit

    override fun engineSetCertificateEntry(alias: String?, cert: Certificate?) = Unit

    override fun engineDeleteEntry(alias: String?) {
        if (alias != null) AndroidKeyStoreKeys.keys.remove(alias)
    }

    override fun engineAliases(): java.util.Enumeration<String> = Collections.enumeration(AndroidKeyStoreKeys.keys.keys)

    override fun engineContainsAlias(alias: String?): Boolean = AndroidKeyStoreKeys.keys.containsKey(alias)

    override fun engineSize(): Int = AndroidKeyStoreKeys.keys.size

    override fun engineIsKeyEntry(alias: String?): Boolean = AndroidKeyStoreKeys.keys.containsKey(alias)

    override fun engineIsCertificateEntry(alias: String?): Boolean = false

    override fun engineGetCertificateAlias(cert: Certificate?): String? = null

    override fun engineStore(stream: java.io.OutputStream?, password: CharArray?) = Unit

    override fun engineLoad(stream: java.io.InputStream?, password: CharArray?) = Unit

    override fun engineLoad(param: KeyStore.LoadStoreParameter?) = Unit
}

internal class FakeAndroidAesKeyGenerator : KeyGeneratorSpi() {
    private var alias: String? = null

    override fun engineInit(random: SecureRandom?) = Unit

    override fun engineInit(params: AlgorithmParameterSpec?, random: SecureRandom?) {
        val spec = params as KeyGenParameterSpec
        alias = spec.keystoreAlias
    }

    override fun engineInit(keysize: Int, random: SecureRandom?) = Unit

    override fun engineGenerateKey(): SecretKey {
        val name = alias ?: error("AndroidKeyStore key has no alias")
        val bytes = ByteArray(32)
        SecureRandom().nextBytes(bytes)
        val key = SecretKeySpec(bytes, "AES")
        AndroidKeyStoreKeys.keys[name] = key
        return key
    }
}
