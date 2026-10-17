package com.grupo8_uniandes.solventa.ui.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.ui.components.SolventaBanner
import com.grupo8_uniandes.solventa.ui.components.SolventaBannerStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButton
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaFieldState
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
    onCreateAccount: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .testTag("screen_login"),
    ) {
        SolventaTopBar(
            title = stringResource(R.string.app_name),
            showBack = true,
            onBack = onBack,
        )
        Column(
            modifier = Modifier
                .verticalScroll(rememberScrollState())
                .padding(SolventaSpacing.gutter),
            verticalArrangement = Arrangement.spacedBy(SolventaSpacing.s16),
        ) {
            Text(
                text = stringResource(R.string.login_heading),
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onSurface,
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
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                visualTransformation = PasswordVisualTransformation(),
                testTag = "field_login_contrasena",
            )
            SolventaButton(
                text = stringResource(R.string.action_ingresar),
                style = SolventaButtonStyle.Filled,
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
    }
}
