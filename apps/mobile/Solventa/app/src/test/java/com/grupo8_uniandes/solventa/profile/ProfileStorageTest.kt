package com.grupo8_uniandes.solventa.profile

import android.Manifest
import android.app.Application
import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.profile.AndroidDevicePermissionReader
import com.grupo8_uniandes.solventa.data.profile.KeySessionOpen
import com.grupo8_uniandes.solventa.data.profile.SessionPrefsFile
import com.grupo8_uniandes.solventa.data.profile.SharedPrefsSessionRepository
import com.grupo8_uniandes.solventa.domain.profile.PermissionKind
import com.grupo8_uniandes.solventa.domain.profile.SignOut
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
class SharedPrefsSessionRepositoryTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Test
    fun givenNoKey_whenRead_thenSessionIsOpen() {
        context.getSharedPreferences(SessionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        val session = SharedPrefsSessionRepository(context)
        assertTrue(session.isOpen())
        assertFalse(
            context.getSharedPreferences(SessionPrefsFile, Context.MODE_PRIVATE)
                .contains(KeySessionOpen),
        )
    }

    @Test
    fun givenSignOut_whenClosed_thenRegistrationIsNotRequired() {
        context.getSharedPreferences(SessionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        val session = SharedPrefsSessionRepository(context)
        SignOut(session)()
        assertFalse(session.isOpen())
        session.open()
        assertTrue(session.isOpen())
    }
}

@RunWith(RobolectricTestRunner::class)
class AndroidDevicePermissionReaderTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Test
    fun givenNothingGranted_whenRead_thenNoRowIsPublished() {
        val rows = AndroidDevicePermissionReader(context).read()
        assertEquals(PermissionKind.entries, rows.map { it.kind })
        assertTrue(rows.none { it.published })
    }

    @Test
    @Config(sdk = [33])
    fun givenCameraAndPhotos_whenRead_thenThoseRowsArePublished() {
        shadowOf(context as Application).grantPermissions(
            Manifest.permission.CAMERA,
            Manifest.permission.READ_MEDIA_IMAGES,
        )
        val rows = AndroidDevicePermissionReader(context).read().associate { it.kind to it.published }
        assertFalse(rows.getValue(PermissionKind.Location))
        assertTrue(rows.getValue(PermissionKind.Camera))
        assertTrue(rows.getValue(PermissionKind.Photos))
        shadowOf(context as Application).denyPermissions(
            Manifest.permission.CAMERA,
            Manifest.permission.READ_MEDIA_IMAGES,
        )
    }

    @Test
    fun givenLocationGranted_whenRead_thenLocationIsPublished() {
        val shadow = shadowOf(context as Application)
        shadow.grantPermissions(Manifest.permission.ACCESS_COARSE_LOCATION)
        assertTrue(published(PermissionKind.Location))
        shadow.denyPermissions(Manifest.permission.ACCESS_COARSE_LOCATION)
        shadow.grantPermissions(Manifest.permission.ACCESS_FINE_LOCATION)
        assertTrue(published(PermissionKind.Location))
        shadow.denyPermissions(Manifest.permission.ACCESS_FINE_LOCATION)
    }

    private fun published(kind: PermissionKind): Boolean =
        AndroidDevicePermissionReader(context).read().first { it.kind == kind }.published

    @Test
    @Config(sdk = [28])
    fun givenLegacyPhotoPermission_whenRead_thenPhotosArePublished() {
        shadowOf(context as Application).grantPermissions(Manifest.permission.READ_EXTERNAL_STORAGE)
        assertTrue(published(PermissionKind.Photos))
        shadowOf(context as Application).denyPermissions(Manifest.permission.READ_EXTERNAL_STORAGE)
    }
}
