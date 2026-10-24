package com.grupo8_uniandes.solventa.data.bff.remote

import com.grupo8_uniandes.solventa.data.bff.dto.ClaimsDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
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
import com.grupo8_uniandes.solventa.data.bff.dto.ProvidersDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushRegistrationDto
import com.grupo8_uniandes.solventa.data.bff.dto.QuoteRequestDto
import com.grupo8_uniandes.solventa.data.bff.dto.RefreshInDto
import com.grupo8_uniandes.solventa.data.bff.dto.RevokeDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionInDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.SignupDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceInDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.WalletDto
import kotlinx.serialization.json.JsonElement
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface MobileBffApi {
    @POST("movil/sesion/ingreso")
    suspend fun signIn(@Body body: SessionInDto): SessionOutDto

    @POST("movil/sesion/refresh")
    suspend fun refresh(@Body body: RefreshInDto): SessionOutDto

    @POST("movil/sesion/refresh")
    fun refreshCall(@Body body: RefreshInDto): Call<SessionOutDto>

    @POST("movil/sesion/salida")
    suspend fun signOut(): Response<ResponseBody>

    @POST("movil/registro")
    suspend fun register(@Body body: SignupDto): SignupDto

    @POST("movil/registro/revocacion")
    suspend fun revoke(@Body body: RevokeDto): RevokeDto

    @POST("movil/cliente/cotizaciones")
    suspend fun quote(
        @Header("Idempotency-Key") key: String,
        @Body body: QuoteRequestDto,
    ): OfferOutDto

    @GET("movil/cliente/cotizaciones/{cotizacionId}")
    suspend fun requote(@Path("cotizacionId") cotizacionId: String): OfferOutDto

    @POST("movil/cliente/polizas")
    suspend fun accept(
        @Header("Idempotency-Key") key: String,
        @Body body: IdDto,
    ): JsonElement

    @GET("movil/cliente/polizas")
    suspend fun wallet(): WalletDto

    @GET("movil/cliente/polizas/{numero}")
    suspend fun detail(@Path("numero") numero: String): DetailDto

    @POST("movil/cliente/siniestros")
    suspend fun notify(
        @Header("Idempotency-Key") key: String,
        @Body body: ClaimNoticeDto,
    ): ClaimReceiptDto

    @GET("movil/cliente/siniestros")
    suspend fun claims(): ClaimsDto

    @GET("movil/cliente/pagos-automaticos")
    suspend fun payment(): PaymentDto

    @POST("movil/cliente/oferta-hipotecaria")
    suspend fun mortgage(@Body body: MortgageInDto): MortgageOutDto

    @GET("movil/cliente/avisos")
    suspend fun notices(): NoticesDto

    @POST("movil/cliente/polizas/{numero}/ciclo")
    suspend fun cycle(
        @Path("numero") numero: String,
        @Header("Idempotency-Key") key: String?,
        @Body body: PolicyCommandDto,
    ): IssuedDto

    @GET("movil/cliente/inicio")
    suspend fun home(): HomeDto

    @POST("movil/cliente/push")
    suspend fun registerPush(@Body body: PushRegistrationDto): PushRegistrationDto

    @GET("movil/cliente/push")
    suspend fun pushNotice(): PushNoticeDto

    @GET("movil/cliente/prestadores")
    suspend fun providers(): ProvidersDto

    @POST("movil/cliente/asistencias")
    suspend fun assistance(@Body body: AssistanceInDto): AssistanceOutDto
}
