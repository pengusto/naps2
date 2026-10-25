// Copyright (c) 2026 Pengusto. GPL-2.0-or-later, like NAPS2.
using System.Runtime.InteropServices;
using Eto.Forms;

namespace NAPS2.Update;

/// <summary>Optional complete-app updater, present only in the independent ES60W bundle.</summary>
internal sealed class ForkUpdateController
{
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int CanInstall();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int StartUpdater(CanInstall callback);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate int State();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate void Action();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] private delegate void SetAutomatic(int enabled);

    private static readonly CanInstall InstallCallback = CanInstallNow;
    private static ForkUpdateController? _current;
    private readonly Form _owner;
    private readonly Func<bool> _busyOrUnsaved;
    private readonly StartUpdater _start;
    private readonly State _state;
    private readonly Action _check;
    private readonly Action _stop;
    private readonly SetAutomatic _setAutomatic;
    private readonly UITimer _timer = new() { Interval = 0.5 };
    private bool _started;
    public Command Check { get; } = new() { MenuText = "Nach ES60W-Updates suchen…", Enabled = false };
    public CheckMenuItem AutomaticChecks { get; } = new() { Text = "Automatisch nach ES60W-Updates suchen", Enabled = false };

    private ForkUpdateController(Form owner, Func<bool> busyOrUnsaved, IntPtr library)
    {
        _owner = owner; _busyOrUnsaved = busyOrUnsaved;
        T Export<T>(string name) where T : Delegate =>
            Marshal.GetDelegateForFunctionPointer<T>(NativeLibrary.GetExport(library, name));
        _start = Export<StartUpdater>("es60w_update_start");
        _state = Export<State>("es60w_update_state");
        _check = Export<Action>("es60w_update_check");
        _stop = Export<Action>("es60w_update_stop");
        _setAutomatic = Export<SetAutomatic>("es60w_update_automatic_checks");
        Check.Executed += (_, _) => _check();
        AutomaticChecks.Click += (_, _) => _setAutomatic(AutomaticChecks.Checked ? 1 : 0);
        _timer.Elapsed += (_, _) => Refresh();
    }

    public static ForkUpdateController? Create(Form owner, Func<bool> busyOrUnsaved)
    {
        var contents = Directory.GetParent(AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar));
        if (contents?.Name != "Contents" ||
            !File.Exists(Path.Combine(contents.FullName, "Resources", "es60w-updates.marker"))) return null;
        var path = Path.Combine(contents.FullName, "Frameworks", "libES60WUpdater.dylib");
        try
        {
            return new ForkUpdateController(owner, busyOrUnsaved, NativeLibrary.Load(path));
        }
        catch (Exception e)
        {
            // Scanning remains available if the optional updater is damaged.
            Log.ErrorException("Could not load ES60W updater", e);
            return null;
        }
    }

    public void Start()
    {
        if (_started) return;
        _current = this;
        _started = _start(InstallCallback) != 0;
        if (!_started)
        {
            MessageBox.Show(_owner, "Der ES60W-Updatekanal konnte nicht gestartet werden.",
                "NAPS2 ES60W", MessageBoxButtons.OK, MessageBoxType.Information);
            return;
        }
        Refresh(); _timer.Start();
    }

    [ObjCRuntime.MonoPInvokeCallback(typeof(CanInstall))]
    private static int CanInstallNow()
    {
        try { return _current != null && !_current._busyOrUnsaved() ? 1 : 0; }
        catch { return 0; }
    }

    private void Refresh()
    {
        var state = _state();
        Check.Enabled = (state & 2) != 0;
        AutomaticChecks.Enabled = (state & 1) != 0;
        AutomaticChecks.Checked = (state & 4) != 0;
    }

    public void Stop()
    {
        _timer.Stop();
        if (_started) _stop();
        if (_current == this) _current = null;
    }
}
