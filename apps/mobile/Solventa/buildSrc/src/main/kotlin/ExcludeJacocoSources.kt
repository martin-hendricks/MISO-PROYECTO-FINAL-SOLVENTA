import org.gradle.api.DefaultTask
import org.gradle.api.file.RegularFileProperty
import org.gradle.api.provider.SetProperty
import org.gradle.api.tasks.Input
import org.gradle.api.tasks.InputFile
import org.gradle.api.tasks.PathSensitive
import org.gradle.api.tasks.PathSensitivity
import org.gradle.api.tasks.TaskAction
import org.w3c.dom.Element
import java.io.File
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.OutputKeys
import javax.xml.transform.TransformerFactory
import javax.xml.transform.dom.DOMSource
import javax.xml.transform.stream.StreamResult

abstract class ExcludeJacocoSources : DefaultTask() {
    @get:InputFile
    @get:PathSensitive(PathSensitivity.NONE)
    abstract val report: RegularFileProperty

    @get:Input
    abstract val excludedSources: SetProperty<String>

    @TaskAction
    fun filter() {
        excludeSourcesFromJacocoReport(report.get().asFile, excludedSources.get())
    }
}

private fun excludeSourcesFromJacocoReport(report: File, excludedSources: Set<String>) {
    if (!report.isFile) return
    val factory = DocumentBuilderFactory.newInstance()
    factory.isValidating = false
    factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false)
    val document = factory.newDocumentBuilder().parse(report)
    val reportElement = document.documentElement
    reportElement.directChildren("package").forEach { pkg ->
        pkg.removeExcludedCoverage(excludedSources)
        if (pkg.directChildren("class").isEmpty() && pkg.directChildren("sourcefile").isEmpty()) {
            reportElement.removeChild(pkg)
        } else {
            pkg.replaceDirectCounters(pkg.sumCountersOf("class"))
        }
    }
    reportElement.replaceDirectCounters(reportElement.sumCountersOf("package"))
    val transformer = TransformerFactory.newInstance().newTransformer()
    transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8")
    transformer.setOutputProperty(OutputKeys.DOCTYPE_PUBLIC, "-//JACOCO//DTD Report 1.1//EN")
    transformer.setOutputProperty(OutputKeys.DOCTYPE_SYSTEM, "report.dtd")
    transformer.transform(DOMSource(document), StreamResult(report))
}

private fun Element.removeExcludedCoverage(excludedSources: Set<String>) {
    val excluded = directChildren("class").filter { it.getAttribute("sourcefilename").isExcludedSource(excludedSources) } +
        directChildren("sourcefile").filter { it.getAttribute("name").isExcludedSource(excludedSources) }
    excluded.forEach(::removeChild)
}

private fun String.isExcludedSource(excludedSources: Set<String>): Boolean =
    this in excludedSources || excludedSources.any { endsWith("/$it") }

private fun Element.sumCountersOf(tag: String): Map<String, Pair<Int, Int>> {
    val totals = linkedMapOf<String, Pair<Int, Int>>()
    directChildren(tag).forEach { child ->
        child.directChildren("counter").forEach { counter ->
            val type = counter.getAttribute("type")
            val missed = counter.getAttribute("missed").toInt() + (totals[type]?.first ?: 0)
            val covered = counter.getAttribute("covered").toInt() + (totals[type]?.second ?: 0)
            totals[type] = missed to covered
        }
    }
    return totals
}

private fun Element.replaceDirectCounters(totals: Map<String, Pair<Int, Int>>) {
    directChildren("counter").forEach(::removeChild)
    totals.forEach { (type, count) ->
        val counter = ownerDocument.createElement("counter")
        counter.setAttribute("type", type)
        counter.setAttribute("missed", count.first.toString())
        counter.setAttribute("covered", count.second.toString())
        appendChild(counter)
    }
}

private fun Element.directChildren(tag: String): List<Element> = buildList {
    val children = childNodes
    for (index in 0 until children.length) {
        val child = children.item(index)
        if (child is Element && child.tagName == tag) add(child)
    }
}
