// Prepared NAPS2 SDK integration; opt-in marker only. MIT + LGPL-2.1-or-later.
#if MAC
using System.Collections.Immutable;
using System.Threading;
using NAPS2.Images;
using NAPS2.Scan;
using NAPS2.Scan.Internal;

namespace NAPS2.Scan.Internal.External;

internal sealed class ExternalSaneScanDriver(ScanningContext context, string helperRoot) : IScanDriver
{
    private readonly ScanImageProcess _helper = new(helperRoot);

    public static string? FindOptInHelper()
    {
        for (var directory = new DirectoryInfo(AppContext.BaseDirectory); directory != null; directory = directory.Parent)
        {
            if (directory.Name != "Contents") continue;
            if (!File.Exists(Path.Combine(directory.FullName, "Resources", "external-scanimage.marker"))) return null;
            var root = Path.Combine(directory.FullName, "Helpers", "ScanHelper.bundle");
            if (!File.Exists(Path.Combine(root, "Contents", "MacOS", "scanimage")))
                throw new IOException("External scan helper missing; refusing native fallback");
            return root;
        }
        return null;
    }

    public async Task GetDevices(ScanOptions options, CancellationToken cancelToken, Action<ScanDevice> callback)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancelToken);
        timeout.CancelAfter(TimeSpan.FromSeconds(20));
        var list = await _helper.RunAsync(["--formatted-device-list=%d\t%v %m%n"], null, timeout.Token);
        foreach (var line in list.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            var fields = line.Split('\t', 2);
            if (fields.Length == 2 && fields[0].StartsWith("epsonds:libusb:", StringComparison.Ordinal)
                && fields[1].Contains("ES-60W", StringComparison.OrdinalIgnoreCase))
                callback(new ScanDevice(Driver.Sane, fields[0], fields[1].Trim()));
        }
    }

    // Deliberately restricted experimental preset, not device capability discovery.
    public Task<ScanCaps> GetCaps(ScanOptions options, CancellationToken cancelToken)
    {
        cancelToken.ThrowIfCancellationRequested();
        return Task.FromResult(new ScanCaps
        {
            PaperSourceCaps = new PaperSourceCaps { SupportsFeeder = true },
            FeederCaps = new PerSourceCaps
            {
                DpiCaps = new DpiCaps { Values = ImmutableList.Create(300) },
                BitDepthCaps = new BitDepthCaps { SupportsColor = true }
            }
        });
    }

    public async Task Scan(ScanOptions options, CancellationToken cancelToken, IScanEvents scanEvents,
        Action<IMemoryImage> callback)
    {
        if (options.Device?.ID.StartsWith("epsonds:libusb:", StringComparison.Ordinal) != true
            || !options.Device.Name.Contains("ES-60W", StringComparison.OrdinalIgnoreCase)
            || options.Dpi != 300 || options.BitDepth != BitDepth.Color
            || options.PaperSource != PaperSource.Feeder || !options.AutoCrop || options.UseNativeUI)
            throw new NotSupportedException("Experimental helper requires ES-60W USB, feeder, 300 dpi color and AutoCrop");
        var directory = Directory.CreateTempSubdirectory("naps2-scanimage-").FullName;
        var image = Path.Combine(directory, "page.tiff");
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancelToken);
        timeout.CancelAfter(TimeSpan.FromMinutes(3));
        try
        {
            scanEvents.PageStart();
            // Ordinary scanimage CLI + lossless standard TIFF, no native ABI in the app.
            await _helper.RunAsync(["--device-name=" + options.Device.ID, "--format=tiff",
                "--source=ADF Front", "--mode=Color", "--depth=8", "--resolution=300",
                "-l", "0", "-t", "0", "-x", "215.89999389648438", "-y", "355.59999084472656",
                "--es60w-auto-length=yes"], image, timeout.Token);
            timeout.Token.ThrowIfCancellationRequested();
            var loaded = context.ImageContext.Load(image);
            callback(loaded);
            scanEvents.PageProgress(1);
        }
        finally { Directory.Delete(directory, recursive: true); }
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
#endif
