package com.grupo8_uniandes.solventa.data.bff.remote

import com.grupo8_uniandes.solventa.data.bff.dto.RefreshInDto
import com.grupo8_uniandes.solventa.data.bff.mapping.bffJson
import com.grupo8_uniandes.solventa.data.bff.mapping.toTokens
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import retrofit2.Retrofit
import java.io.IOException
import java.util.UUID
import java.util.concurrent.TimeUnit

class BffClients(
    val api: MobileBffApi,
) {
    companion object {
        fun open(address: String, tokens: TokenStore, readTimeoutSeconds: Long = 5): BffClients {
            val refreshApi = retrofit(address, refreshClient(readTimeoutSeconds)).create(MobileBffApi::class.java)
            val authed = refreshClient(readTimeoutSeconds).newBuilder()
                .addInterceptor(AccessInterceptor(tokens))
                .authenticator(RefreshAuthenticator(tokens, refreshApi))
                .build()
            return BffClients(retrofit(address, authed).create(MobileBffApi::class.java))
        }

        private fun refreshClient(readTimeoutSeconds: Long): OkHttpClient =
            OkHttpClient.Builder()
                .addInterceptor(CorrelationInterceptor())
                .retryOnConnectionFailure(false)
                .connectTimeout(readTimeoutSeconds, TimeUnit.SECONDS)
                .readTimeout(readTimeoutSeconds, TimeUnit.SECONDS)
                .writeTimeout(readTimeoutSeconds, TimeUnit.SECONDS)
                .build()

        private fun retrofit(address: String, client: OkHttpClient): Retrofit {
            val base = if (address.endsWith("/")) address else "$address/"
            return Retrofit.Builder()
                .baseUrl(base)
                .client(client)
                .addConverterFactory(bffJson.asConverterFactory("application/json".toMediaType()))
                .build()
        }
    }
}

internal fun newIdempotencyKey(): String = UUID.randomUUID().toString()

private class CorrelationInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .header("X-Correlation-Id", UUID.randomUUID().toString())
            .build()
        return chain.proceed(request)
    }
}

private class AccessInterceptor(private val tokens: TokenStore) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        if (request.url.encodedPath.isOpenSession()) return chain.proceed(request)
        val access = tokens.read()?.accessToken
        if (access.isNullOrBlank()) return chain.proceed(request)
        return chain.proceed(
            request.newBuilder().header("Authorization", "Bearer $access").build(),
        )
    }
}

private class RefreshAuthenticator(
    private val tokens: TokenStore,
    private val refreshApi: MobileBffApi,
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): Request? {
        if (response.request.url.encodedPath.isOpenSession()) return null
        if (response.request.header(RETRY) != null || response.priorResponse != null) {
            tokens.clear()
            return null
        }
        val current = tokens.read() ?: return null
        val refreshed = synchronized(this) {
            runBlocking {
                try {
                    refreshApi.refreshCall(RefreshInDto(current.refreshToken)).execute()
                } catch (_: IOException) {
                    null
                }
            }
        }
        val body = refreshed?.body()
        if (refreshed == null || !refreshed.isSuccessful || body == null) {
            tokens.clear()
            return null
        }
        tokens.save(body.toTokens())
        return response.request.newBuilder()
            .header("Authorization", "Bearer ${body.accessToken}")
            .header(RETRY, "1")
            .build()
    }

    private companion object {
        const val RETRY = "X-Auth-Retry"
    }
}

private fun String.isOpenSession(): Boolean =
    endsWith("sesion/ingreso") || endsWith("sesion/refresh")
