// Own UI entry point; opts in only for the independently packaged ES-60W app. MIT.
using Eto.Forms;
using NAPS2.Scan;
using NAPS2.EtoForms.Ui;

namespace NAPS2.EtoForms.Desktop;

internal sealed class ScannerButtonController
{
    private readonly ScannerButtonSession _session;
    private readonly DesktopForm _form;
    private readonly IProfileManager _profiles;
    private readonly IDesktopScanController _scans;
    private readonly Func<bool> _hasActiveOperations;
    private bool _stopped;
    public ActionCommand Command { get; }

    public static ScannerButtonController? Create(DesktopForm form, IProfileManager profiles,
        IDesktopScanController scans, Func<bool> hasActiveOperations)
    {
        var resources = Paths.FreeScannerResources;
        if (resources == null || !File.Exists(Path.Combine(resources, "scanner-button.marker"))) return null;
        var executable = Path.GetFullPath(Path.Combine(resources, "..", "Helpers", "ScanHelper.bundle",
            "Contents", "MacOS", "scanner-button"));
        if (!File.Exists(executable)) throw new IOException("Bundled scanner button receiver missing");
        return new ScannerButtonController(form, profiles, scans, hasActiveOperations, executable);
    }

    private ScannerButtonController(DesktopForm form, IProfileManager profiles,
        IDesktopScanController scans, Func<bool> hasActiveOperations, string executable)
    {
        _form = form; _profiles = profiles; _scans = scans; _hasActiveOperations = hasActiveOperations;
        Command = new ActionCommand(Toggle) { Text = "Scannertaste aktivieren" };
        var transport = new ScannerButtonTransport(executable,
            Path.Combine(Paths.AppData, "scanner-button.lock"),
            () => { if (!_stopped) Command.Text = "Scannertaste: bereit (deaktivieren)"; },
            () => { if (!_stopped) Command.Text = "Scannertaste: wartet auf USB … (deaktivieren)"; },
            Path.Combine(Paths.AppData, "scanner-button.log"));
        _session = new ScannerButtonSession(transport.WaitAsync, ConfirmAndScan, Error);
        ScannerButtonGate.Session = _session;
    }
    private async Task Toggle()
    {
        if (_session.Enabled)
        {
            await _session.DisableAsync(); Command.Text = "Scannertaste aktivieren";
        }
        else
        {
            Command.Text = "Scannertaste verbinden … (deaktivieren)";
            _session.Enable();
        }
    }
    private bool Busy() => _hasActiveOperations()
        || Application.Instance.Windows.Any(w => w is Dialog && w.Visible);

    private async Task ConfirmAndScan(ScannerButtonSignal signal)
    {
        if (Busy()) return;
        var profile = _profiles.DefaultProfile;
        if (profile == null || profile.DriverName != "sane" || profile.UseNativeUI
            || profile.Resolution.Dpi != 300 || profile.BitDepth != ScanBitDepth.C24Bit
            || profile.PaperSource != ScanSource.Feeder || !profile.AutoCrop
            || (profile.Device != null && !ScannerButtonProtocol.CanBindDevice(
                profile.Device.ID, profile.Device.Name, signal.DeviceId)))
        {
            Error(new InvalidOperationException("Bitte das ES-60W-Standardprofil mit 300 dpi, Farbe, Einzug und AutoCrop wählen."));
            return;
        }
        _form.BringToFront();
        if (MessageBox.Show(_form, "Scannertaste gedrückt. Eingelegtes Blatt jetzt scannen?",
                "ES-60W", MessageBoxButtons.YesNo, MessageBoxType.Question,
                MessageBoxDefaultButton.Yes) != DialogResult.Yes || !_session.Enabled || Busy()) return;
        // Bind this operation to the emitting USB device, without rewriting a saved profile.
        var selected = profile.Clone();
        selected.Device = new ScanProfileDevice(signal.DeviceId, "Epson ES-60W");
        Command.Text = "Scannertaste: Scan läuft";
        await _scans.ScanFromButton(selected);
    }
    private void Error(Exception error)
    {
        if (_stopped) return;
        _ = _session.DisableAsync();
        Command.Text = "Scannertaste aktivieren";
        MessageBox.Show(_form, "Scannertaste nicht bereit. " + error.Message,
            "ES-60W", MessageBoxButtons.OK, MessageBoxType.Information);
    }
    public void Stop()
    {
        _stopped = true;
        ScannerButtonGate.Session = null;
        _ = _session.DisableAsync();
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
