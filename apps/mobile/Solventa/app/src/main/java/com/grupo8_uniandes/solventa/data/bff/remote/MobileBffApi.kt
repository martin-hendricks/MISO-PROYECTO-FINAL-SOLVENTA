package com.grupo8_uniandes.solventa.data.bff.remote

import com.grupo8_uniandes.solventa.data.bff.dto.AccountNameDto
import com.grupo8_uniandes.solventa.data.bff.dto.AcceptedQuoteDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimsDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimDetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimReceiptDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.dto.IdDto
import com.grupo8_uniandes.solventa.data.bff.dto.IssuedDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageInDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.NoticesDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.PaymentDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyCommandDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProfilingConsentDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProvidersDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushRegistrationDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushTokenRetiroDto
import com.grupo8_uniandes.solventa.data.bff.dto.QuoteRequestDto
import com.grupo8_uniandes.solventa.data.bff.dto.RefreshInDto
import com.grupo8_uniandes.solventa.data.bff.dto.RevokeDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionInDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.LivenessResultDto
import com.grupo8_uniandes.solventa.data.bff.dto.LivenessUpdateDto
import com.grupo8_uniandes.solventa.data.bff.dto.SignupDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceInDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.BilleteraDto
import com.grupo8_uniandes.solventa.data.bff.dto.MovimientoDto
import com.grupo8_uniandes.solventa.data.bff.dto.PoliciesDto
import kotlinx.serialization.json.JsonElement
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Response
import com.grupo8_uniandes.solventa.data.bff.dto.RenewalPreferenceDto
import com.grupo8_uniandes.solventa.data.bff.dto.RenewalRequestDto
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.HTTP
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface MobileBffApi {
    @POST("sesion/ingreso")
    suspend fun signIn(@Body body: SessionInDto): SessionOutDto

    @POST("sesion/refresh")
    suspend fun refresh(@Body body: RefreshInDto): SessionOutDto

    @POST("sesion/refresh")
    fun refreshCall(@Body body: RefreshInDto): Call<SessionOutDto>

    @POST("sesion/salida")
    suspend fun signOut(): Response<ResponseBody>

    @POST("registro")
    suspend fun register(@Body body: SignupDto): SignupDto

    @Multipart
    @POST("identidad/prueba-de-vida")
    suspend fun checkLiveness(@Part foto: MultipartBody.Part): LivenessResultDto

    @PATCH("cliente/prueba-de-vida")
    suspend fun recordLiveness(@Body body: LivenessUpdateDto): LivenessUpdateDto

    @POST("registro/revocacion")
    suspend fun revoke(@Body body: RevokeDto): RevokeDto

    @POST("cliente/cotizaciones")
    suspend fun quote(
        @Header("Idempotency-Key") key: String,
        @Body body: QuoteRequestDto,
    ): OfferOutDto

    @GET("cliente/cotizaciones/{cotizacionId}")
    suspend fun requote(@Path("cotizacionId") cotizacionId: String): OfferOutDto

    @POST("cliente/cotizaciones/{cotizacionId}/aceptacion")
    suspend fun acceptQuote(
        @Header("Idempotency-Key") key: String,
        @Path("cotizacionId") cotizacionId: String,
    ): AcceptedQuoteDto

    @POST("cliente/polizas")
    suspend fun accept(
        @Header("Idempotency-Key") key: String,
        @Body body: IdDto,
    ): JsonElement

    @GET("cliente/polizas")
    suspend fun policies(): PoliciesDto

    @GET("cliente/billetera")
    suspend fun billetera(): BilleteraDto

    @GET("cliente/billetera/{id}")
    suspend fun movimiento(@Path("id") id: String): MovimientoDto

    @GET("cliente/polizas/{numero}")
    suspend fun detail(@Path("numero") numero: String): DetailDto

    @Multipart
    @POST("cliente/siniestros")
    suspend fun notify(
        @Header("Idempotency-Key") key: String,
        @Part parts: List<MultipartBody.Part>,
    ): ClaimReceiptDto

    @GET("cliente/siniestros")
    suspend fun claims(): ClaimsDto

    @GET("cliente/siniestros/{id}")
    suspend fun claim(@Path("id") id: String): ClaimDetailDto

    @GET("cliente/pagos-automaticos")
    suspend fun payment(): PaymentDto

    @POST("cliente/oferta-hipotecaria")
    suspend fun mortgage(@Body body: MortgageInDto): MortgageOutDto

    @GET("cliente/consentimiento-perfil")
    suspend fun profilingConsent(): ProfilingConsentDto

    @DELETE("cliente/consentimiento-perfil")
    suspend fun revokeProfilingConsent(): ProfilingConsentDto

    @GET("cliente/avisos")
    suspend fun notices(): NoticesDto

    @PATCH("cliente/polizas/{numero}/preferencias")
    suspend fun preferences(
        @Path("numero") numero: String,
        @Body body: RenewalRequestDto,
    ): RenewalPreferenceDto

    @POST("cliente/polizas/{numero}/ciclo")
    suspend fun cycle(
        @Path("numero") numero: String,
        @Header("Idempotency-Key") key: String?,
        @Body body: PolicyCommandDto,
    ): IssuedDto

    @GET("cliente/inicio")
    suspend fun home(): HomeDto

    @GET("cliente/perfil")
    suspend fun accountName(): AccountNameDto

    @PATCH("cliente/perfil")
    suspend fun saveAccountName(@Body body: AccountNameDto): AccountNameDto

    @POST("cliente/avisos/token")
    suspend fun registerPush(@Body body: PushRegistrationDto): Response<ResponseBody>

    @HTTP(method = "DELETE", path = "cliente/avisos/token", hasBody = true)
    suspend fun unregisterPush(@Body body: PushTokenRetiroDto): Response<ResponseBody>

    @GET("cliente/prestadores")
    suspend fun providers(): ProvidersDto

    @POST("cliente/asistencias")
    suspend fun assistance(@Body body: AssistanceInDto): AssistanceOutDto
}
