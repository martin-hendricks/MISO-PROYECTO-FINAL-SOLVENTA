package com.grupo8_uniandes.solventa.ui.login

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
import com.grupo8_uniandes.solventa.ui.components.SolventaPasswordToggle
import com.grupo8_uniandes.solventa.ui.components.SolventaTextField
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.theme.SolventaSpacing

@Composable
fun LoginScreen(
    email: String,
    password: String,
    failure: LoginFailure,
    onEmail: (String) -> Unit,
    onPassword: (String) -> Unit,
    onIngresar: () -> Unit,
    onBack: () -> Unit,
    showBack: Boolean = true,
    onCreateAccount: () -> Unit,
    onBiometric: () -> Unit,
    biometricEnabled: Boolean = false,
    biometricFallback: Boolean = false,
    confirmBiometric: Boolean = false,
    onAcceptBiometric: () -> Unit = {},
    onDeclineBiometric: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    var passwordVisible by remember { mutableStateOf(false) }
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.surface)
            .testTag("screen_login"),
    ) {
        SolventaTopBar(
            title = stringResource(R.string.app_name),
            showBack = showBack,
            onBack = onBack,
        )
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
        ) {
            Text(
                text = stringResource(loginHeading(biometricEnabled, biometricFallback)),
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Text(
                text = stringResource(loginSupport(biometricEnabled, biometricFallback)),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (failure == LoginFailure.Rejected) {
                SolventaBanner(
                    message = stringResource(R.string.login_error_banner),
                    style = SolventaBannerStyle.Error,
                )
            }
            if (failure == LoginFailure.Unavailable) {
                SolventaBanner(
                    message = stringResource(R.string.login_unavailable_banner),
                    style = SolventaBannerStyle.Error,
                )
            }
            SolventaTextField(
                value = email,
                onValueChange = onEmail,
                label = stringResource(R.string.login_email),
                helper = "",
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                testTag = "field_login_correo",
            )
            SolventaTextField(
                value = password,
                onValueChange = onPassword,
                label = stringResource(R.string.login_password),
                helper = if (failure == LoginFailure.Rejected) {
                    stringResource(R.string.login_error_password)
                } else {
                    ""
                },
                state = if (failure == LoginFailure.Rejected) {
                    SolventaFieldState.Error
                } else {
                    SolventaFieldState.Default
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = if (passwordVisible) KeyboardType.Text else KeyboardType.Password,
                ),
                visualTransformation = if (passwordVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                trailingIcon = {
                    SolventaPasswordToggle(
                        visible = passwordVisible,
                        onToggle = { passwordVisible = !passwordVisible },
                        testTag = "toggle_login_contrasena",
                    )
                },
                testTag = "field_login_contrasena",
            )
            val biometricOffered = biometricEnabled && !biometricFallback
            if (biometricOffered) {
                SolventaButton(
                    text = stringResource(R.string.action_usar_biometria),
                    style = SolventaButtonStyle.Filled,
                    onClick = onBiometric,
                    modifier = Modifier.fillMaxWidth(),
                    testTag = "action_biometric",
                )
            }
            SolventaButton(
                text = stringResource(R.string.action_ingresar),
                style = if (biometricOffered) {
                    SolventaButtonStyle.Outlined
                } else {
                    SolventaButtonStyle.Filled
                },
                onClick = onIngresar,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_ingresar",
            )
            SolventaButton(
                text = stringResource(R.string.action_crear_cuenta),
                style = SolventaButtonStyle.Text,
                onClick = onCreateAccount,
                modifier = Modifier.fillMaxWidth(),
                testTag = "action_crear_cuenta",
            )
        }
        if (confirmBiometric) {
            AlertDialog(
                onDismissRequest = onDeclineBiometric,
                title = { Text(stringResource(R.string.login_biometric_title)) },
                text = { Text(stringResource(R.string.login_biometric_confirm)) },
                confirmButton = {
                    TextButton(onClick = onAcceptBiometric) {
                        Text(stringResource(R.string.action_biometric_accept))
                    }
                },
                dismissButton = {
                    TextButton(onClick = onDeclineBiometric) {
                        Text(stringResource(R.string.action_biometric_decline))
                    }
                },
            )
        }
    }
}

internal fun loginHeading(biometricEnabled: Boolean, biometricFallback: Boolean): Int = when {
    biometricEnabled && biometricFallback -> R.string.login_biometric_fallback_title
    biometricEnabled -> R.string.login_biometric_heading
    else -> R.string.login_heading
}

internal fun loginSupport(biometricEnabled: Boolean, biometricFallback: Boolean): Int = when {
    biometricEnabled && biometricFallback -> R.string.login_biometric_fallback_support
    biometricEnabled -> R.string.login_biometric_support
    else -> R.string.login_support
}
