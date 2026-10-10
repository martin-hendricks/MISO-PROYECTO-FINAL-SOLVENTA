package com.grupo8_uniandes.solventa.data.region

import android.content.Context
import android.content.SharedPreferences
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.domain.region.RegionRepository

internal const val RegionPrefsFile = "region_prefs"
internal const val KeyAppliedRegion = "applied_region"
internal const val KeyDraftRegion = "draft_region"
internal const val KeyFirstLaunchCompleted = "first_launch_completed"

class SharedPrefsRegionRepository(
    private val prefs: SharedPreferences,
) : RegionRepository {
    constructor(context: Context) : this(
        context.applicationContext.getSharedPreferences(
            RegionPrefsFile,
            Context.MODE_PRIVATE,
        ),
    )

    override fun read(): RegionChoice = RegionChoice(
        appliedRegion = Region.fromStored(prefs.getString(KeyAppliedRegion, null)),
        draftRegion = Region.fromStored(prefs.getString(KeyDraftRegion, null)),
        firstLaunchCompleted = prefs.getBoolean(KeyFirstLaunchCompleted, false),
    )

    override fun stage(region: Region): RegionChoice {
        val next = read().copy(draftRegion = region)
        write(next)
        return next
    }

    override fun confirmFirstLaunch(): RegionChoice {
        val current = read()
        val next = current.copy(
            appliedRegion = current.draftRegion,
            firstLaunchCompleted = true,
        )
        write(next)
        return next
    }

    override fun confirmFromProfile(): RegionChoice {
        val current = read()
        val next = current.copy(appliedRegion = current.draftRegion)
        write(next)
        return next
    }

    private fun write(choice: RegionChoice) {
        prefs.edit()
            .putString(KeyAppliedRegion, choice.appliedRegion.languageTag)
            .putString(KeyDraftRegion, choice.draftRegion.languageTag)
            .putBoolean(KeyFirstLaunchCompleted, choice.firstLaunchCompleted)
            .commit()
    }
}

fun readAppliedLanguageTag(context: Context): String =
    readAppliedLanguageTag(
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE),
    )

internal fun readAppliedLanguageTag(prefs: SharedPreferences): String {
    val raw = prefs.getString(KeyAppliedRegion, null)
    return Region.fromStored(raw).languageTag
}
