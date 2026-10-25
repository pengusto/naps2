// Original process adapter; no native SANE API or private RPC. MIT (repository LICENSE).
using System.Diagnostics;
using System.Text;
using System.Threading;

namespace NAPS2.Scan.Internal.External;

internal sealed class ScanImageProcess(string root, bool synthetic = false)
{
    public async Task<string> RunAsync(IEnumerable<string> arguments, string? tiff,
        CancellationToken cancelToken)
    {
        cancelToken.ThrowIfCancellationRequested();
        if (tiff != null && File.Exists(tiff)) throw new IOException("Output already exists");
        var bundled = Directory.Exists(Path.Combine(root, "Contents", "MacOS"));
        if (bundled && synthetic) throw new IOException("Production helper bundle has no synthetic backend");
        var config = bundled ? Path.Combine(root, "Contents", "Resources", "config")
            : Path.Combine(root, synthetic ? "test-support/config" : "config");
        if (File.ReadAllText(Path.Combine(config, "dll.conf")).Trim() != (synthetic ? "test" : "epsonds"))
            throw new IOException("Unexpected helper backend configuration");
        if (!synthetic && !File.Exists(Path.Combine(config, "epsonds.conf")))
            throw new IOException("USB configuration missing; refusing system fallback");
        var executable = bundled ? Path.Combine(root, "Contents", "MacOS", "scanimage")
            : Path.Combine(root, "bin", "scanimage");
        var start = new ProcessStartInfo(executable)
        {
            UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true,
            CreateNoWindow = true
        };
        foreach (var key in start.Environment.Keys.ToArray())
            if (key.StartsWith("DYLD_") || key.StartsWith("SANE_") ||
                key is "LD_LIBRARY_PATH" or "LIBPATH" or "SHLIB_PATH") start.Environment.Remove(key);
        start.Environment["SANE_CONFIG_DIR"] = config;
        start.Environment["LD_LIBRARY_PATH"] = bundled ? Path.Combine(root, "Contents", "Frameworks", "sane")
            : Path.Combine(root, synthetic ? "test-support/backends" : "lib/sane");
        start.Environment["LC_ALL"] = "C";
        foreach (var argument in arguments) start.ArgumentList.Add(argument);
        using var proc = Process.Start(start) ?? throw new IOException("Cannot start scanimage");
        void Kill() { try { if (!proc.HasExited) proc.Kill(entireProcessTree: true); } catch (InvalidOperationException) { } }
        using var registration = cancelToken.Register(Kill);
        using var text = new MemoryStream();
        bool ownsOutput = false;
        try
        {
            // CreateNew prevents overwriting user data. Caller chooses a new private temporary path.
            using Stream output = tiff == null ? text : new FileStream(tiff, FileMode.CreateNew, FileAccess.Write);
            ownsOutput = tiff != null;
            var stdout = Pump();
            var stderr = ReadError();
            await Task.WhenAll(stdout, stderr, proc.WaitForExitAsync(CancellationToken.None));
            cancelToken.ThrowIfCancellationRequested();
            if (proc.ExitCode != 0) throw new IOException($"scanimage exited {proc.ExitCode}: {stderr.Result}");
            return tiff == null ? Encoding.UTF8.GetString(text.ToArray()) : "";

            async Task Pump()
            {
                try
                {
                    var buffer = new byte[65536];
                    long total = 0;
                    int count;
                    while ((count = await proc.StandardOutput.BaseStream.ReadAsync(buffer, cancelToken)) != 0)
                    {
                        total += count;
                        if (total > (tiff == null ? 1024 * 1024 : 256L * 1024 * 1024))
                            throw new IOException("scanimage output exceeds limit");
                        await output.WriteAsync(buffer.AsMemory(0, count), cancelToken);
                    }
                }
                catch { Kill(); throw; }
            }
            async Task<string> ReadError()
            {
                var error = new StringBuilder();
                var buffer = new char[4096];
                int count;
                while ((count = await proc.StandardError.ReadAsync(buffer)) != 0)
                    if (error.Length < 65536) error.Append(buffer, 0, Math.Min(count, 65536 - error.Length));
                return error.ToString();
            }
        }
        catch
        {
            Kill();
            await proc.WaitForExitAsync(CancellationToken.None);
            if (ownsOutput) File.Delete(tiff!);
            cancelToken.ThrowIfCancellationRequested();
            throw;
        }
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
