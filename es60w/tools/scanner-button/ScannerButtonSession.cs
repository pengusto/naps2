// Own opt-in button lifecycle; no hardware, UI or vendor dependency. MIT.
using System.Threading;

namespace NAPS2.Scan;

internal sealed record ScannerButtonSignal(string DeviceId, int Button);

internal sealed class ScannerButtonSession(
    Func<CancellationToken, Task<ScannerButtonSignal?>> wait,
    Func<ScannerButtonSignal, Task> accept,
    Action<Exception> error)
{
    private CancellationTokenSource? _waitCancel;
    private Task<ScannerButtonSignal?>? _wait;
    private Task? _loop;
    private int _pauses;
    public bool Enabled { get; private set; }

    // Invoked on the application's UI context, just like Pause/Disable.
    public void Enable()
    {
        Enabled = true;
        StartIfIdle();
    }
    private void StartIfIdle()
    {
        if (Enabled && _pauses == 0 && (_loop == null || _loop.IsCompleted)) _loop = Loop();
    }
    public async Task DisableAsync()
    {
        Enabled = false;
        await CancelWait();
    }
    public async Task<IDisposable> PauseAsync()
    {
        _pauses++;
        await CancelWait();
        return new Lease(() => { _pauses--; StartIfIdle(); });
    }
    private async Task CancelWait()
    {
        _waitCancel?.Cancel();
        if (_wait != null)
            try { await _wait; } catch (OperationCanceledException) { } catch (Exception) { }
    }
    private async Task Loop()
    {
        try
        {
            // Prevent a synchronously completed fake or failed process from racing assignment of _loop.
            await Task.Yield();
            while (Enabled && _pauses == 0)
            {
                using var cancel = new CancellationTokenSource();
                _waitCancel = cancel;
                _wait = wait(cancel.Token);
                var signal = await _wait;
                _wait = null; _waitCancel = null;
                if (signal == null)
                {
                    // Missing/reconnected USB and clean EOF are idle states, not button events.
                    // Keep opt-in enabled, bound retry frequency, and enumerate anew next time.
                    await Task.Delay(750);
                    continue;
                }
                if (!Enabled || _pauses != 0) break;
                await accept(signal);
                // One process/event at a time, including confirmation and scan completion.
                await Task.Delay(1000);
            }
        }
        catch (OperationCanceledException) { }
        catch (Exception e) { Enabled = false; error(e); }
        finally
        {
            _wait = null; _waitCancel = null;
            _loop = null;
            StartIfIdle();
        }
    }
    private sealed class Lease(Action release) : IDisposable
    {
        private Action? _release = release;
        public void Dispose() => Interlocked.Exchange(ref _release, null)?.Invoke();
    }
}

internal static class ScannerButtonGate
{
    public static ScannerButtonSession? Session { get; set; }
    public static Task<IDisposable> PauseAsync() => Session?.PauseAsync()
        ?? Task.FromResult<IDisposable>(new EmptyLease());
    private sealed class EmptyLease : IDisposable { public void Dispose() { } }
}
