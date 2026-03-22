package com.taptogo.taptogo

import android.content.Intent
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Bundle
import java.io.File
import java.util.Locale

/**
 * MainActivity with NFC foreground dispatch.
 * Writes NFC tag UID to nfc_scan.tmp for Flet to poll.
 * UID format: "04:A3:2F:BC" (uppercase hex with colons).
 */
class MainActivity : io.flutter.embedding.android.FlutterActivity() {

    private var nfcAdapter: NfcAdapter? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
    }

    override fun onResume() {
        super.onResume()
        nfcAdapter?.let { adapter ->
            val intent = Intent(this, javaClass).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
            val pendingIntent = android.app.PendingIntent.getActivity(
                this, 0, intent,
                android.app.PendingIntent.FLAG_MUTABLE or android.app.PendingIntent.FLAG_UPDATE_CURRENT
            )
            try {
                adapter.enableForegroundDispatch(this, pendingIntent, null, null)
            } catch (e: SecurityException) {
                // NFC permission not granted
            }
        }
    }

    override fun onPause() {
        super.onPause()
        nfcAdapter?.disableForegroundDispatch(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (NfcAdapter.ACTION_NDEF_DISCOVERED == intent.action ||
            NfcAdapter.ACTION_TAG_DISCOVERED == intent.action ||
            NfcAdapter.ACTION_TECH_DISCOVERED == intent.action
        ) {
            val tag: Tag? = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG)
            tag?.let { writeNfcUid(it) }
        }
    }

    private fun writeNfcUid(tag: Tag) {
        val uid = tag.id
        val hex = uid.joinToString(":") { b -> "%02X".format(Locale.US, b and 0xff) }
        try {
            val file = File(filesDir, "nfc_scan.tmp")
            file.writeText(hex)
        } catch (e: Exception) {
            // Ignore write errors
        }
    }
}
