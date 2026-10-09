package com.grupo8_uniandes.solventa.navigation

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class CustomerNavHostTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenDefaultStart_whenShown_thenInicio() {
        rule.setContent {
            SolventaTheme {
                CustomerNavHost(
                    navController = rememberNavController(),
                    homeState = HomeUiState(),
                    contentPadding = PaddingValues(0.dp),
                )
            }
        }

        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
    }

    @Test
    fun givenProfileStart_whenShown_thenPerfil() {
        rule.setContent {
            SolventaTheme {
                CustomerNavHost(
                    navController = rememberNavController(),
                    homeState = HomeUiState(),
                    contentPadding = PaddingValues(0.dp),
                    startDestination = PerfilRoute,
                )
            }
        }

        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
    }
}
