using NAPS2.Scan;

namespace NAPS2.EtoForms.Desktop;

public interface IDesktopScanController
{
    Task ScanWithDevice(string deviceID);
    Task ScanDefault();
    Task ScanWithNewProfile();
    Task ScanWithProfile(ScanProfile profile);
    Task ScanFromButton(ScanProfile profile);
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
