// Overlay: customiza o MainActivity do template do Flet.
// Mantém o papel original (FlutterActivity do app Flet) e adiciona um
// watcher de APK pendente: o Python escreve um marcador na pasta de dados
// do app e o Android abre a tela de instalação sozinho em seguida.
//
// O único passo manual que o Android permite é o "Instalar" final na
// janela do sistema — nenhum app pode instalar APK sozinho fora da Play Store.
package {{ cookiecutter.org_name_2 }}.{{ cookiecutter.package_name }}

import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.core.content.FileProvider
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import java.io.File

class MainActivity : FlutterActivity() {

    private val tag = "EronsfireInstaller"
    private val markerName = "install_pending.txt"
    private val handler = Handler(Looper.getMainLooper())

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        startInstallPendingPoll()
    }

    /**
     * Pastas onde o Python pode ter deixado o marcador. O primeiro argumento
     * (filesDir) é o Context.getFilesDir(); o segundo é o irmão
     * <filesDir>/data, que é o FLET_APP_STORAGE_DATA do Python/Flet.
     * getExternalFilesDir(null) cobre dispositivo/variant legacy.
     */
    private fun candidateDirs(): List<File> {
        val dirs = mutableListOf(
            context.filesDir,
            File(context.filesDir, "data"),
            context.cacheDir,
            getExternalFilesDir(null)
        )
        return dirs
    }

    /** Reconsome um APK pendente (se houver) e dispara o instalador. */
    private fun consumePendingInstall() {
        for (dir in candidateDirs()) {
            val marker = File(dir, markerName)
            if (!marker.exists()) continue

            try {
                val content = marker.readText(Charsets.UTF_8).trim()
                val apk = if (File(content).isAbsolute) File(content) else File(dir, content)

                if (!apk.exists() || apk.length() < 1_000_000L) {
                    Log.w(tag, "Marcador aponta para APK inválido; ignorando: ${apk.absolutePath}")
                    marker.delete()
                    continue
                }

                val uri = FileProvider.getUriForFile(
                    context,
                    context.packageName + ".provider",
                    apk
                )
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, "application/vnd.android.package-archive")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
                }
                startActivity(intent)
                Log.i(tag, "Instalador aberto para ${apk.absolutePath}")
                marker.delete()
                return
            } catch (e: Exception) {
                Log.e(tag, "Falha ao abrir o instalador: ${e.message}", e)
                // Se o marcador continuar travado, remove para não prender o fluxo.
                marker.delete()
            }
        }
    }

    private fun startInstallPendingPoll() {
        val runnable = object : Runnable {
            override fun run() {
                try {
                    consumePendingInstall()
                } catch (e: Exception) {
                    Log.e(tag, "Erro inesperado no poll: ${e.message}", e)
                } finally {
                    handler.postDelayed(this, 1_000L)
                }
            }
        }
        handler.postDelayed(runnable, 1_000L)
    }
}
