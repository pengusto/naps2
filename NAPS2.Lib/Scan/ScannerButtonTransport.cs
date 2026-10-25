// Own bounded text protocol for the bundled interrupt receiver. MIT.
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

namespace NAPS2.Scan;

internal static class ScannerButtonProtocol
{
    private static bool UsbId(string? id) => id != null && Regex.IsMatch(id, @"\Aepsonds:libusb:[0-9]{3}:[0-9]{3}\z");
    public static bool CanBindDevice(string? savedId, string? savedName, string actual) => UsbId(actual) &&
        (savedId == null || savedId == actual || UsbId(savedId) &&
            (savedName == "ES-60W (epsonds)" || string.Equals(savedName, "Epson ES-60W", StringComparison.OrdinalIgnoreCase)));
    public static bool IsRetry(string? line) => line is "retry\tmissing" or "retry\tdisconnected" or "retry\tbusy";
    public static string ParseReady(string? line)
    {
        var parts = line?.Split('\t');
        if (parts?.Length != 2 || parts[0] != "ready"
            || !Regex.IsMatch(parts[1], @"\Aepsonds:libusb:[0-9]{3}:[0-9]{3}\z"))
            throw new IOException("Invalid scanner button readiness response");
        return parts[1];
    }
    public static ScannerButtonSignal ParseButton(string? line, string device)
    {
        var parts = line?.Split('\t');
        if (parts?.Length != 3 || parts[0] != "button" || parts[2] != device
            || !byte.TryParse(parts[1], out var number))
            throw new IOException("Invalid scanner button event");
        return new ScannerButtonSignal(device, number);
    }
}

internal sealed class ScannerButtonTransport(string executable, string lockFile, Action ready,
    Action? waiting = null, string? diagnosticFile = null)
{
    public async Task<ScannerButtonSignal?> WaitAsync(CancellationToken cancel)
    {
        cancel.ThrowIfCancellationRequested();
        var start = new ProcessStartInfo(executable) { UseShellExecute = false,
            RedirectStandardOutput = true, RedirectStandardError = true, CreateNoWindow = true };
        foreach (var key in start.Environment.Keys.ToArray())
            if (key.StartsWith("DYLD_") || key.StartsWith("SANE_") ||
                key is "LD_LIBRARY_PATH" or "LIBPATH" or "SHLIB_PATH") start.Environment.Remove(key);
        start.ArgumentList.Add("--listen"); start.ArgumentList.Add(lockFile);
        using var process = Process.Start(start) ?? throw new IOException("Cannot start button receiver");
        Log("receiver pid=" + process.Id);
        void Stop() { try { if (!process.HasExited) _ = KillSignal(process.Id, 15); }
            catch (InvalidOperationException) { } }
        using var registration = cancel.Register(Stop);
        var errors = ReadError();
        try
        {
            var first = await process.StandardOutput.ReadLineAsync(cancel);
            cancel.ThrowIfCancellationRequested();
            if (first == null || ScannerButtonProtocol.IsRetry(first)) return await Retry(first);
            if (first.Length > 256) throw new IOException("Button response too long");
            var device = ScannerButtonProtocol.ParseReady(first);
            Log("ready " + device); ready();
            var line = await process.StandardOutput.ReadLineAsync(cancel);
            cancel.ThrowIfCancellationRequested();
            if (line == null || ScannerButtonProtocol.IsRetry(line)) return await Retry(line);
            if (line?.Length > 256) throw new IOException("Button event too long");
            var signal = ScannerButtonProtocol.ParseButton(line, device);
            if (await process.StandardOutput.ReadLineAsync(cancel) != null)
                throw new IOException("More than one button event from one receiver");
            await process.WaitForExitAsync(cancel);
            cancel.ThrowIfCancellationRequested();
            if (process.ExitCode != 0) throw new IOException(await errors);
            Log("button accepted after receiver exit " + signal.Button);
            // The USB interface is already closed and the process has exited here.
            return signal;
        }
        finally
        {
            Stop();
            using var shutdown = new CancellationTokenSource(TimeSpan.FromSeconds(2));
            try { await process.WaitForExitAsync(shutdown.Token); }
            catch (OperationCanceledException)
            {
                if (!process.HasExited) process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync(CancellationToken.None);
            }
            Log((await errors).Trim());
        }
        async Task<ScannerButtonSignal?> Retry(string? line)
        {
            await process.WaitForExitAsync(cancel);
            cancel.ThrowIfCancellationRequested();
            // A clean EOF has no button. It must not become a parser error or scan.
            // Explicit reconnect notices additionally require the temporary-failure exit.
            if (line != null && process.ExitCode != 75 || line == null && process.ExitCode is not (0 or 75))
                throw new IOException("Button receiver stopped: " + await errors);
            Log("waiting " + (line ?? "clean EOF") + " exit=" + process.ExitCode);
            waiting?.Invoke();
            return null;
        }
        async Task<string> ReadError()
        {
            var text = new StringBuilder(); var buffer = new char[2048]; int count;
            while ((count = await process.StandardError.ReadAsync(buffer).ConfigureAwait(false)) != 0)
                if (text.Length < 16384) text.Append(buffer, 0, Math.Min(count, 16384-text.Length));
            return text.ToString();
        }
    }
    private void Log(string message)
    {
        if (diagnosticFile == null || message.Length == 0) return;
        try
        {
            if (File.Exists(diagnosticFile) && new FileInfo(diagnosticFile).Length > 131072)
                File.Move(diagnosticFile, diagnosticFile + ".previous", overwrite: true);
            File.AppendAllText(diagnosticFile, DateTimeOffset.Now.ToString("O") + " " + message + "\n");
        }
        catch (IOException) { } catch (UnauthorizedAccessException) { }
    }
    [DllImport("libSystem.B.dylib", EntryPoint = "kill", SetLastError = true)]
    private static extern int KillSignal(int pid, int signal);
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
