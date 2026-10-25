using System.Collections.Concurrent;
using NAPS2.Scan;

var context = new Pump();
SynchronizationContext.SetSynchronizationContext(context);
var run = Check();
while (!run.IsCompleted) context.Step();
await run;

static async Task Check()
{
    int cases = 0;
    void Assert(bool ok) { if (!ok) throw new Exception("Control failed at case " + cases); }
    async Task Eventually(Func<bool> condition)
    {
        var until = DateTime.UtcNow.AddSeconds(3);
        while (!condition()) { if (DateTime.UtcNow > until) throw new Exception("Timed out"); await Task.Delay(5); }
    }
    var device = "epsonds:libusb:001:005";
    Assert(ScannerButtonProtocol.ParseReady("ready\t"+device) == device); cases++;
    Assert(ScannerButtonProtocol.ParseButton("button\t0\t"+device, device).Button == 0); cases++;
    foreach (var wrong in new[] { "button\t0\tother", "button\t256\t"+device, "button\t-1\t"+device, "ready\t"+device, "" })
    {
        try { ScannerButtonProtocol.ParseButton(wrong, device); throw new Exception("Invalid event accepted"); }
        catch (IOException) { cases++; }
    }
    foreach (var wrong in new[] { "ready\tapple:device", "ready\t"+device+"\textra", "ready\tepsonds:libusb:1:5" })
    {
        try { ScannerButtonProtocol.ParseReady(wrong); throw new Exception("Invalid ready accepted"); }
        catch (IOException) { cases++; }
    }
    int waits=0, accepted=0, errors=0, active=0;
    TaskCompletionSource<ScannerButtonSignal?>? pending=null;
    var session = new ScannerButtonSession(async cancel => {
        waits++; active++;
        pending = new(TaskCreationOptions.RunContinuationsAsynchronously);
        try { return await pending.Task.WaitAsync(cancel); }
        finally { active--; }
    }, _ => { accepted++; return Task.CompletedTask; }, _ => errors++);
    session.Enable(); await Eventually(() => active==1);
    using (var first = await session.PauseAsync())
    {
        Assert(active==0); cases++;
        using (var second = await session.PauseAsync())
        { session.Enable(); await Task.Delay(20); Assert(active==0); cases++; }
        await Task.Delay(20); Assert(active==0); cases++;
    }
    await Eventually(() => active==1 && waits==2);
    await session.DisableAsync(); await Task.Delay(20);
    Assert(active==0 && accepted==0 && errors==0 && !session.Enabled); cases++;

    var confirmation = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
    int serialWaits=0, serialAccepts=0;
    var serial = new ScannerButtonSession(_ => { serialWaits++; return Task.FromResult<ScannerButtonSignal?>(new(device,1)); },
        async _ => { serialAccepts++; await confirmation.Task; }, _ => errors++);
    serial.Enable(); await Eventually(() => serialAccepts==1);
    await Task.Delay(30); Assert(serialWaits==1 && serialAccepts==1); cases++;
    await serial.DisableAsync(); confirmation.SetResult(); await Task.Delay(1100);
    Assert(serialWaits==1 && !serial.Enabled); cases++;

    int failures=0;
    var failed = new ScannerButtonSession(_ => throw new IOException("busy"), _ => Task.CompletedTask, _ => failures++);
    failed.Enable(); await Eventually(() => failures==1); await Task.Delay(30);
    Assert(!failed.Enabled && failures==1); cases++;
    var ended = new ScannerButtonSession(_ => Task.FromResult<ScannerButtonSignal?>(null), _ => Task.CompletedTask, _ => errors++);
    ended.Enable(); await Task.Delay(30); Assert(ended.Enabled); cases++;
    await ended.DisableAsync();

    int reconnectWaits = 0, reconnectAccepts = 0;
    var reconnect = new ScannerButtonSession(_ => Task.FromResult<ScannerButtonSignal?>(
        ++reconnectWaits == 1 ? null : new("epsonds:libusb:001:009", 0)),
        _ => { reconnectAccepts++; return Task.CompletedTask; }, _ => errors++);
    reconnect.Enable(); await Eventually(() => reconnectAccepts == 1);
    await reconnect.DisableAsync();
    Assert(reconnectWaits == 2 && reconnectAccepts == 1); cases++;
    Assert(ScannerButtonProtocol.CanBindDevice(device,"Epson ES-60W","epsonds:libusb:001:009")); cases++;
    Assert(ScannerButtonProtocol.CanBindDevice(device,"ES-60W (epsonds)","epsonds:libusb:001:009")); cases++;
    Assert(!ScannerButtonProtocol.CanBindDevice(device,"Other scanner","epsonds:libusb:001:009")); cases++;
    Assert(!ScannerButtonProtocol.CanBindDevice("apple:other","Epson ES-60W","epsonds:libusb:001:009")); cases++;
    Assert(!ScannerButtonProtocol.CanBindDevice(null,null,"wrong")); cases++;

    // A late packet from a receiver which ignores cancellation cannot start a paused operation.
    var latePacket = new TaskCompletionSource<ScannerButtonSignal?>(TaskCreationOptions.RunContinuationsAsynchronously);
    int lateAccepts=0;
    var late = new ScannerButtonSession(_ => latePacket.Task, _ => { lateAccepts++; return Task.CompletedTask; }, _ => errors++);
    late.Enable(); await Task.Delay(20);
    var pause=late.PauseAsync(); latePacket.SetResult(new(device,0));
    using (await pause) { Assert(lateAccepts==0); cases++; await late.DisableAsync(); }

    var args = Environment.GetCommandLineArgs();
    if (args.Length == 3)
    {
        var path=Path.Combine(args[2],"good"); int ready=0;
        var transport = new ScannerButtonTransport(args[1],path,()=>ready++);
        var signal = await transport.WaitAsync(CancellationToken.None);
        Assert(ready==1 && signal?.Button==0 && File.Exists(path+".released")); cases++;
        var pid=int.Parse(File.ReadAllText(path+".pid"));
        Assert(!Alive(pid)); cases++;
        transport = new ScannerButtonTransport(args[1],Path.Combine(args[2],"bad"),()=>{});
        try { await transport.WaitAsync(CancellationToken.None); throw new Exception("Wrong process event accepted"); }
        catch (IOException) { cases++; }
        foreach (var scenario in new[] { "retry-before", "eof", "disconnect" })
        {
            int notices = 0;
            transport = new ScannerButtonTransport(args[1],Path.Combine(args[2],scenario),()=>{},()=>notices++);
            Assert(await transport.WaitAsync(CancellationToken.None) == null && notices == 1); cases++;
        }
        foreach (var scenario in new[] { "bad-retry", "fail-eof", "multiple" })
        {
            transport = new ScannerButtonTransport(args[1],Path.Combine(args[2],scenario),()=>{});
            try { await transport.WaitAsync(CancellationToken.None); throw new Exception("Malformed process accepted"); }
            catch (IOException) { cases++; }
        }
        path=Path.Combine(args[2],"hold");
        using var cancel=new CancellationTokenSource();
        var seenReady=new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        transport = new ScannerButtonTransport(args[1],path,()=>seenReady.SetResult());
        var waiting=transport.WaitAsync(cancel.Token);
        await seenReady.Task; cancel.Cancel();
        try { await waiting; throw new Exception("Cancellation ignored"); }
        catch (OperationCanceledException) { cases++; }
        Assert(!Alive(int.Parse(File.ReadAllText(path+".pid")))); cases++;
    }
    Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new { controls_passed=cases, hardware_scans=0, device_commands=0 }));
}

static bool Alive(int pid)
{
    try { using var process=System.Diagnostics.Process.GetProcessById(pid); return !process.HasExited; }
    catch (ArgumentException) { return false; }
}

sealed class Pump : SynchronizationContext
{
    private readonly BlockingCollection<(SendOrPostCallback,object?)> _queue = new();
    public override void Post(SendOrPostCallback callback, object? state) => _queue.Add((callback,state));
    public void Step() { if (_queue.TryTake(out var work,100)) work.Item1(work.Item2); }
}
