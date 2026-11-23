package com.grupo8_uniandes.solventa.claim

import android.graphics.Bitmap
import android.graphics.Color
import com.grupo8_uniandes.solventa.ui.shell.fetchEvidenceThumb
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okio.Buffer
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.io.ByteArrayOutputStream

@RunWith(RobolectricTestRunner::class)
class EvidenceThumbTest {
    @Test
    fun givenAUrlThatIsNotHttp_whenFetched_thenNothingIsReturned() = runBlocking {
        assertNull(fetchEvidenceThumb("memoria://bucket/foto.jpg"))
        assertNull(fetchEvidenceThumb(""))
    }

    @Test
    fun givenAJpegOnTheServer_whenFetched_thenTheBitmapIsThatPhoto() = runBlocking {
        val server = MockWebServer()
        server.enqueue(MockResponse().setBody(Buffer().write(jpeg())))
        server.start()
        try {
            assertNotNull(fetchEvidenceThumb(server.url("/foto.jpg").toString()))
        } finally {
            server.shutdown()
        }
    }

    @Test
    fun givenAFailureOrAnEmptyBody_whenFetched_thenNothingIsReturned() = runBlocking {
        val server = MockWebServer()
        server.enqueue(MockResponse().setResponseCode(404))
        server.enqueue(MockResponse().setBody(""))
        server.start()
        try {
            val base = server.url("/").toString().trimEnd('/')
            assertNull(fetchEvidenceThumb("$base/missing"))
            assertNull(fetchEvidenceThumb("$base/empty"))
            assertNull(fetchEvidenceThumb("http://127.0.0.1:1/down"))
        } finally {
            server.shutdown()
        }
    }

    private fun jpeg(): ByteArray {
        val bitmap = Bitmap.createBitmap(4, 4, Bitmap.Config.ARGB_8888)
        bitmap.eraseColor(Color.RED)
        val out = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, out)
        return out.toByteArray()
    }
}
