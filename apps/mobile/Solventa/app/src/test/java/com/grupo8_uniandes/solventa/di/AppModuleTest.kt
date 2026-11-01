package com.grupo8_uniandes.solventa.di

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.mock.MockMobileSessionRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockOfferRepository
import com.grupo8_uniandes.solventa.data.bff.remote.RemoteOfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.region.Region
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.koin.android.ext.koin.androidContext
import org.koin.core.annotation.KoinExperimentalAPI
import org.koin.dsl.koinApplication
import org.koin.test.verify.verify
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class AppModuleTest {
    @OptIn(KoinExperimentalAPI::class)
    @Test
    fun graphResolvesWithContextSuppliedOutsideTheModule() {
        appModule("").verify(
            extraTypes = listOf(
                Context::class,
                String::class,
                Boolean::class,
                Region::class,
            ),
        )
    }

    @Test
    fun emptyAddressResolvesTheStandIn() {
        val koin = koinApplication {
            androidContext(ApplicationProvider.getApplicationContext())
            modules(appModule(""))
        }.koin
        assertTrue(koin.get<OfferRepository>() is MockOfferRepository)
        assertTrue(koin.get<MobileSessionRepository>() is MockMobileSessionRepository)
    }

    @Test
    fun namedAddressResolvesOneRemoteClient() {
        val koin = koinApplication {
            androidContext(ApplicationProvider.getApplicationContext())
            modules(appModule("http://127.0.0.1:9"))
        }.koin
        assertTrue(koin.get<OfferRepository>() is RemoteOfferRepository)
        assertTrue(koin.get<MobileSessionRepository>() !is MockMobileSessionRepository)
    }

    @Test
    fun startingTwiceKeepsTheSameGraph() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        startSolventaKoin(context)
        startSolventaKoin(context)
        val koin = org.koin.core.context.GlobalContext.get()
        assertTrue(koin.get<OfferRepository>() === koin.get<OfferRepository>())
    }
}
