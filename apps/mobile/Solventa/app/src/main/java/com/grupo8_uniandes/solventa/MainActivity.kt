package com.grupo8_uniandes.solventa

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.grupo8_uniandes.solventa.ui.shell.CustomerShell
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SolventaTheme {
                CustomerShell()
            }
        }
    }
}
