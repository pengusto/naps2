using NAPS2.Images;
using NAPS2.Images.Bitwise;
using NAPS2.Images.Transforms;
using System.Text.Json;

if (args.Length == 4)
{
    int w = int.Parse(args[1]), h = int.Parse(args[2]);
    byte[] source = File.ReadAllBytes(args[0]);
    if (source.LongLength != (long)w * h * 3) throw new Exception("RGB length mismatch");
    var op = new DarkBackingPageImageOp();
    op.Perform(source, new PixelInfo(w, h, SubPixelType.Rgb));
    object result;
    if (op.Frame is { } frame)
    {
        var g = frame.Geometry(w, h);
        var destination = new byte[g.width * g.height * 3];
        new PaperFrameImageOp(frame).Perform(source, new PixelInfo(w, h, SubPixelType.Rgb),
            destination, new PixelInfo(g.width, g.height, SubPixelType.Rgb));
        File.WriteAllBytes(args[3], destination);
        result = new { mode = "paper-frame", width = g.width, height = g.height,
            frame.Left, frame.Right, frame.Slope, frame.Top, frame.Bottom,
            frame.PaperLeft, frame.PaperRight, frame.PaperTop, frame.PaperBottom, u = g.u, v = g.v, c = g.c, s = g.s };
    }
    else
    {
        var width = new DarkBackingWidthImageOp(); width.Perform(source, new PixelInfo(w, h, SubPixelType.Rgb));
        int ow = w - width.Left - width.Right;
        var destination = new byte[ow * h * 3];
        for (int y = 0; y < h; y++) Array.Copy(source, (y * w + width.Left) * 3, destination, y * ow * 3, ow * 3);
        File.WriteAllBytes(args[3], destination);
        result = new { mode = "conservative-width-fallback", width = ow, height = h,
            left = width.Left, right = width.Right };
    }
    Console.WriteLine(JsonSerializer.Serialize(result));
    return;
}
int passed = 0;
void Assert(bool condition, string message) { if (!condition) throw new Exception(message); }

foreach (var format in new[] { SubPixelType.Rgb, SubPixelType.Bgr, SubPixelType.Rgba, SubPixelType.Bgra, SubPixelType.Rgbn })
foreach (bool invertY in new[] { false, true })
foreach (double slope in new[] { -.015, 0, .015 })
{
    const int w = 1000, h = 700;
    var info = new PixelInfo(w, h, format, strideAlign: 16) { InvertY = invertY };
    var source = new byte[info.Length];
    // A blank sheet reaches the first and last input rows: losing either is a regression.
    for (int y = 0; y < h; y++)
    for (int x = 0; x < w; x++)
    {
        byte value = x >= 200 + slope * y && x < 800 + slope * y ? (byte)240 : (byte)30;
        int at = (invertY ? h - 1 - y : y) * info.Stride + x * format.BytesPerPixel;
        for (int k = 0; k < format.BytesPerPixel; k++) source[at + k] = value;
    }
    byte[] before = (byte[])source.Clone();
    var op = new DarkBackingPageImageOp(); op.Perform(source, info);
    Assert(op.Frame != null, $"missing frame {format} {invertY} {slope}");
    var frame = op.Frame!; var g = frame.Geometry(w, h);
    Assert(Math.Abs(frame.Slope - slope) < .001, "incorrect skew");
    Assert(g.width >= 600 && g.width < 625 && g.height >= h, "unexpected bounds");
    for (int y = 0; y < h; y++)
    foreach (double x in new[] { Math.Ceiling(200 + slope * y), Math.Ceiling(800 + slope * y) - 1 })
    {
        double u = g.c * x - g.s * y - g.u, v = g.s * x + g.c * y - g.v;
        Assert(u >= 0 && u <= g.width - 1 && v >= 0 && v <= g.height - 1, "source paper edge excluded");
    }
    var dstInfo = new PixelInfo(g.width, g.height, format, strideAlign: 16) { InvertY = !invertY };
    byte[] dst = new byte[dstInfo.Length];
    new PaperFrameImageOp(frame).Perform(source, info, dst, dstInfo);
    Assert(source.SequenceEqual(before), "source changed");
    int middle = (dstInfo.InvertY ? g.height - 1 - g.height / 2 : g.height / 2) * dstInfo.Stride + g.width / 2 * format.BytesPerPixel;
    Assert(dst[middle] == 240, "pixel format/inverted row regression");
    if (slope == 0)
    {
        Assert(g.height == h, "unskewed height changed");
        // Unskewed framing is an exact copy, including top and bottom rows.
        for (int y = 0; y < h; y++)
        for (int x = 0; x < g.width; x++)
        for (int k = 0; k < (format.HasAlpha ? 4 : 3); k++)
        {
            int si = (invertY ? h - 1 - y : y) * info.Stride + ((int)frame.Left + x) * format.BytesPerPixel + k;
            int di = (dstInfo.InvertY ? h - 1 - y : y) * dstInfo.Stride + x * format.BytesPerPixel + k;
            Assert(source[si] == dst[di], "unskewed RGB/alpha changed");
        }
    }
    passed++;
}

foreach (string kind in new[] { "full-width", "dark-paper", "light-backing", "tiny", "nonparallel", "colored-outside" })
{
    var info = new PixelInfo(1000, 700, SubPixelType.Rgb);
    var bytes = new byte[info.Length];
    for (int y = 0; y < info.Height; y++)
    for (int x = 0; x < info.Width; x++)
    {
        double left = kind == "tiny" ? 450 : 200, right = kind == "tiny" ? 490 : 800;
        if (kind == "nonparallel") right += y * .015;
        bool paper = kind == "full-width" || x >= left && x < right;
        byte value = paper ? (kind == "dark-paper" ? (byte)100 : (byte)240) :
            kind == "light-backing" ? (byte)125 : (byte)30;
        int p = (y * info.Width + x) * 3;
        bytes[p] = bytes[p + 1] = bytes[p + 2] = value;
        if (kind == "colored-outside" && x < 100) { bytes[p] = 130; bytes[p + 1] = bytes[p + 2] = 5; }
    }
    var op = new DarkBackingPageImageOp(); op.Perform(bytes, info);
    Assert(op.Frame == null, "ambiguous image cropped: " + kind);
    passed++;
}
// Near-full-width backing was the old early-return bug.
{
    var info = new PixelInfo(1000, 700, SubPixelType.Rgb); var bytes = new byte[info.Length];
    for (int y = 0; y < 700; y++) for (int x = 0; x < 1000; x++)
        for (int c = 0; c < 3; c++) bytes[(y * 1000 + x) * 3 + c] = (byte)(x >= 15 && x < 985 ? 240 : 30);
    var op = new DarkBackingPageImageOp(); op.Perform(bytes, info);
    Assert(op.Frame != null && op.Frame.Geometry(1000, 700).width < 1000, "thin backing not removed"); passed++;
}
// A small top-edge protrusion is invisible to a central-90%-height margin metric.
// The all-row envelope must retain it even when most paper edges fit a straight line.
{
    const int w = 1000, h = 700;
    var info = new PixelInfo(w, h, SubPixelType.Rgbn); var source = new byte[info.Length];
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
    {
        int left = y < 20 ? 190 : 200;
        byte value = x >= left && x < 800 ? (byte)240 : (byte)30;
        for (int c = 0; c < 3; c++) source[y * info.Stride + x * 4 + c] = value;
    }
    byte[] before = (byte[])source.Clone();
    var op = new DarkBackingPageImageOp(); op.Perform(source, info);
    Assert(op.Frame != null, "curved edge unexpectedly rejected");
    var g = op.Frame!.Geometry(w, h);
    double protrusion = g.c * 190 - g.s * 10 - g.u;
    Assert(protrusion >= 0 && protrusion < 7, "top edge envelope or counterexample lost");
    Assert(source.SequenceEqual(before), "curved-edge source changed");
    passed++;
}
{
    var serializer = new NAPS2.Serialization.XmlSerializer<List<Transform>>();
    var original = new PaperFrameTransform(12.25, 2489.5, .008, 2544, 3438);
    var copy = serializer.DeserializeFromXDocument(serializer.SerializeToXDocument(new List<Transform> { original }));
    Assert(copy?.Count == 1 && copy[0] is PaperFrameTransform restored && restored == original,
        "paper frame cannot be restored from undo/recovery XML");
    passed++;
}
// Photo fallback: textured dark print must not depend on white pixel coverage.
foreach (var format in new[] { SubPixelType.Rgb, SubPixelType.Bgr, SubPixelType.Rgba, SubPixelType.Bgra, SubPixelType.Rgbn })
foreach (bool inverted in new[] { false, true })
foreach (string kind in new[] { "right", "left", "full", "uniform-dark", "corner-mark", "thin-mark", "dark-mark", "protrusion" })
{
    const int w=1000,h=700;
    var info=new PixelInfo(w,h,format,strideAlign:16){InvertY=inverted};
    var bytes=new byte[info.Length];
    for(int y=0;y<h;y++) for(int x=0;x<w;x++)
    {
        bool paper=kind=="left" ? x>=500 : x<500;
        if(kind=="full") paper=true;
        if(kind=="protrusion" && y<20 && x<540) paper=true;
        int at=(inverted?h-1-y:y)*info.Stride+x*format.BytesPerPixel;
        byte v=(byte)(paper ? (kind=="uniform-dark"?100:70+(x*17+y*7)%91) : 30);
        bytes[at+format.RedOffset]=v;
        bytes[at+format.GreenOffset]=(byte)(paper?v:34);
        bytes[at+format.BlueOffset]=(byte)(paper?v:40);
        if(format.BytesPerPixel==4) bytes[at+3]=211;
        if((kind=="corner-mark" && x>=850 && x<853 && y>=2 && y<5) ||
           (kind=="thin-mark" && x==850 && y>=2 && y<14))
            for(int k=0;k<3;k++) bytes[at+k]=240;
        if(kind=="dark-mark" && x==850 && y>=2 && y<14)
            for(int k=0;k<3;k++) bytes[at+k]=85;
    }
    var before=(byte[])bytes.Clone();
    var op=new DarkBackingWidthImageOp();op.Perform(bytes,info);
    if(kind=="right") Assert(op.Left==0 && op.Right>470 && op.Right<500,"photo right width");
    else if(kind=="left") Assert(op.Right==0 && op.Left>470 && op.Left<500,"photo left width");
    else Assert(op.Left==0 && op.Right==0,"ambiguous/outside mark cropped: "+kind);
    Assert(bytes.SequenceEqual(before),"photo source mutated");
    passed++;
}
// Extra margin may shrink only beside a visible pale lip. Tiny visible marks,
// dark coherent strokes, colored points and first/last-row protrusions retain
// the original guard. Test both byte orders, padded stride and inverted rows.
foreach (var format in new[] { SubPixelType.Rgb, SubPixelType.Bgr, SubPixelType.Rgba, SubPixelType.Bgra, SubPixelType.Rgbn })
foreach (bool inverted in new[] { false, true })
foreach (string kind in new[] { "clean", "mirrored", "sparse-lip", "short-lip", "no-lip", "white-point", "color-point", "dark-stroke", "top-protrusion", "bottom-protrusion", "dark-block" })
{
    const int w=1000,h=700;
    var info=new PixelInfo(w,h,format,strideAlign:16){InvertY=inverted};
    var bytes=new byte[info.Length];
    for(int y=0;y<h;y++) for(int x=0;x<w;x++)
    {
        int logical=kind=="mirrored" ? w-1-x : x;
        bool paper=logical<500;
        byte v=(byte)(paper ? 70+(logical*17+y*7)%91 : 30);
        int at=(inverted?h-1-y:y)*info.Stride+x*format.BytesPerPixel;
        bytes[at+format.RedOffset]=v;
        bytes[at+format.GreenOffset]=(byte)(paper?v:34);
        bytes[at+format.BlueOffset]=(byte)(paper?v:40);
        if(format.BytesPerPixel==4) bytes[at+3]=211;
        if(kind!="no-lip" && (kind!="short-lip" || y<70) && (kind!="sparse-lip" || y%10==0) && logical>=496 && logical<500)
            bytes[at+format.RedOffset]=bytes[at+format.GreenOffset]=bytes[at+format.BlueOffset]=225;
        bool bright=(kind=="white-point" && logical==506 && y==0) ||
            (kind=="top-protrusion" && logical>=500 && logical<507 && y<3) ||
            (kind=="bottom-protrusion" && logical>=500 && logical<507 && y>=h-3);
        if(bright) bytes[at+format.RedOffset]=bytes[at+format.GreenOffset]=bytes[at+format.BlueOffset]=240;
        if(kind=="color-point" && logical==506 && y==h-1)
        {bytes[at+format.RedOffset]=110;bytes[at+format.GreenOffset]=20;bytes[at+format.BlueOffset]=20;}
        if((kind=="dark-stroke" && logical==506 && y<7) ||
            (kind=="dark-block" && logical>=505 && logical<507 && y>=100 && y<102))
            bytes[at+format.RedOffset]=bytes[at+format.GreenOffset]=bytes[at+format.BlueOffset]=85;
    }
    var before=(byte[])bytes.Clone();
    var op=new DarkBackingWidthImageOp();op.Perform(bytes,info);
    int end=w-op.Right-op.Left;
    if(kind is "clean" or "mirrored" or "sparse-lip") Assert(end>=500 && end<=504,"excess photo safety margin: "+kind+" "+end);
    else if(kind is "no-lip" or "short-lip") Assert(end==508,"ambiguous edge tightened");
    else Assert(end>=507 && end<=508,"margin guard lost visible/ambiguous pixels: "+kind+" "+end);
    Assert(bytes.SequenceEqual(before),"refinement mutated source");
    passed++;
}
// Four-edge refinement: verify every known source content pixel survives both
// output bounds and exterior clearing, across skew, pixel layout and row order.
foreach (var format in new[] { SubPixelType.Rgb, SubPixelType.Bgra, SubPixelType.Rgbn })
foreach (bool inverted in new[] { false, true })
foreach (double slope in new[] { -.025, 0, .025 })
{
    const int w = 1000, h = 700;
    var info = new PixelInfo(w, h, format, strideAlign: 16) { InvertY = inverted };
    var source = new byte[info.Length];
    var ink = new List<(int x, int y)>();
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
    {
        double u = x - slope * y, v = y + slope * x;
        bool paper = u >= 160 && u < 840 && v >= 130 && v < 570;
        // Print within 8 pixels of ALL four edges, plus an interior cross.
        bool mark = paper && ((u >= 168 && u < 172 || u >= 828 && u < 832) && v > 200 && v < 240 ||
            (v >= 138 && v < 142 || v >= 558 && v < 562) && u > 450 && u < 500);
        byte value = mark ? (byte)15 : paper ? (byte)240 : (byte)30;
        int at = (inverted ? h - 1 - y : y) * info.Stride + x * format.BytesPerPixel;
        for (int k = 0; k < format.BytesPerPixel; k++) source[at + k] = value;
        if (mark) ink.Add((x, y));
    }
    var before = (byte[])source.Clone();
    var op = new DarkBackingPageImageOp(); op.Perform(source, info);
    var frame = op.Frame;
    Assert(frame?.Top != null && frame.Bottom != null, "four-edge frame missing");
    var g = frame!.Geometry(w, h);
    Assert(Math.Abs(frame.Slope - slope) < .001, "rectangle edge skew incorrect");
    foreach (var point in ink)
    {
        double u = g.c * point.x - g.s * point.y, v = g.s * point.x + g.c * point.y;
        Assert(u - g.u >= 0 && u - g.u <= g.width - 1 && v - g.v >= 0 && v - g.v <= g.height - 1,
            "known near-edge content outside output");
        Assert((frame.PaperLeft == null || u >= frame.PaperLeft * g.c) &&
               (frame.PaperRight == null || u < frame.PaperRight * g.c) &&
               (frame.PaperTop == null || v >= frame.PaperTop * g.c) &&
               (frame.PaperBottom == null || v < frame.PaperBottom * g.c), "known content cleared as backing");
    }
    var dstInfo = new PixelInfo(g.width, g.height, format, strideAlign: 16) { InvertY = !inverted };
    var dst = new byte[dstInfo.Length];
    new PaperFrameImageOp(frame).Perform(source, info, dst, dstInfo);
    Assert(source.SequenceEqual(before), "rectangle changed original");
    int dark = 0;
    for (int y = 0; y < g.height; y++) for (int x = 0; x < g.width; x++)
    {
        int at = (dstInfo.InvertY ? g.height - 1 - y : y) * dstInfo.Stride + x * format.BytesPerPixel;
        if (dst[at] < 100) dark++;
    }
    Assert(dark >= ink.Count * .8, "rendered near-edge print lost");
    passed++;
}
// New horizontal fields survive the same recovery/undo XML used by the app.
{
    var serializer = new NAPS2.Serialization.XmlSerializer<List<Transform>>();
    var frame = new PaperFrameTransform(12, 900, .01, 1000, 700)
        { Top = 10, Bottom = 650, PaperLeft = 13, PaperRight = 899, PaperTop = 11, PaperBottom = 649 };
    var restored = serializer.DeserializeFromXDocument(serializer.SerializeToXDocument(new List<Transform> { frame }));
    Assert(restored?.Single() == frame, "horizontal/exterior frame recovery serialization failed");
    passed++;
}
// A closed printed border can enclose a larger white area than the actual
// paper margin. It must NOT become a new four-edge crop through that border.
foreach (double slope in new[] { -.025, 0, .025 })
{
    const int w = 1000, h = 700;
    var info = new PixelInfo(w, h, SubPixelType.Rgb);
    var source = new byte[info.Length];
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
    {
        double u = x - slope * y, v = y + slope * x;
        bool paper = u >= 160 && u < 840 && v >= 130 && v < 570;
        bool border = paper && ((u >= 168 && u < 172 || u >= 828 && u < 832) && v >= 138 && v < 562 ||
            (v >= 138 && v < 142 || v >= 558 && v < 562) && u >= 168 && u < 832);
        byte value = border ? (byte)15 : paper ? (byte)240 : (byte)30;
        for (int k = 0; k < 3; k++) source[(y * w + x) * 3 + k] = value;
    }
    var before = (byte[])source.Clone();
    var op = new DarkBackingPageImageOp(); op.Perform(source, info);
    Assert(op.Frame?.Top == null, "printed border mistaken for paper height");
    Assert(source.SequenceEqual(before), "ambiguous source changed");
    passed++;
}
// Large-angle paper: printed marks within two pixels of every corner must remain
// within BOTH the enclosing canvas and the exterior-fill predicates.
foreach (var format in new[] { SubPixelType.Rgb, SubPixelType.Bgra, SubPixelType.Rgbn })
foreach (bool inverted in new[] { false, true })
foreach (int centerY in new[] { 300, 500 })
foreach (int edgeInset in new[] { 2, 5 })
foreach (double degrees in new[] { -39, -30, -15, 15, 30, 39 })
{
    const int w = 1000, h = 1000;
    double radians = degrees * Math.PI / 180, c = Math.Cos(radians), s = Math.Sin(radians);
    var info = new PixelInfo(w,h,format,strideAlign:16) { InvertY = inverted };
    var bytes = new byte[info.Length]; var ink = new List<(int x,int y)>();
    for (int y=0;y<h;y++) for(int x=0;x<w;x++)
    {
        double u=c*(x-500)-s*(y-centerY), v=s*(x-500)+c*(y-centerY);
        bool paper = Math.Abs(u)<=320 && Math.Abs(v)<=190;
        // Short edge/corner marks, not a closed dark frame.
        bool mark = paper && (Math.Abs(u)>310-edgeInset+2 && Math.Abs(u)<320-edgeInset && Math.Abs(v)>178-edgeInset+2 && Math.Abs(v)<190-edgeInset ||
                              Math.Abs(u)<25 && Math.Abs(v)>178-edgeInset+2 && Math.Abs(v)<190-edgeInset);
        byte value = mark ? (byte)15 : paper ? (byte)240 : (byte)30;
        int at=(inverted?h-1-y:y)*info.Stride+x*format.BytesPerPixel;
        for(int k=0;k<format.BytesPerPixel;k++) bytes[at+k]=value;
        if(mark) ink.Add((x,y));
    }
    var before=(byte[])bytes.Clone(); var op=new DarkBackingPageImageOp();op.Perform(bytes,info);
    var frame=op.Frame; Assert(frame?.Top!=null,"large-angle rectangle missing: "+degrees);
    Assert(Math.Abs(Math.Atan(frame!.Slope)*180/Math.PI-degrees)<.3,"large-angle estimate");
    var g=frame.Geometry(w,h);
    foreach(var point in ink)
    {
        double u=g.c*point.x-g.s*point.y,v=g.s*point.x+g.c*point.y;
        Assert(u-g.u>=0 && u-g.u<=g.width-1 && v-g.v>=0 && v-g.v<=g.height-1,"large-angle print outside canvas");
        Assert((frame.PaperLeft==null || u>=frame.PaperLeft*g.c) &&
               (frame.PaperRight==null || u<frame.PaperRight*g.c) &&
               (frame.PaperTop==null || v>=frame.PaperTop*g.c) &&
               (frame.PaperBottom==null || v<frame.PaperBottom*g.c),"large-angle print cleared");
    }
    var dstInfo=new PixelInfo(g.width,g.height,format,strideAlign:16) { InvertY=!inverted };
    var output=new byte[dstInfo.Length];new PaperFrameImageOp(frame).Perform(bytes,info,output,dstInfo);
    Assert(bytes.SequenceEqual(before),"large-angle source modified");
    passed++;
}
// Exterior marks / printed-frame ambiguity must not be swallowed as scanner
// dust by the large-angle refinement. One isolated dust pixel is tolerated.
foreach (string kind in new[] { "dust", "exterior-mark", "printed-frame", "dark-photo", "white-backing", "triangle" })
{
    const int w=1000,h=1000; double c=Math.Cos(Math.PI/6),s=Math.Sin(Math.PI/6);
    var info=new PixelInfo(w,h,SubPixelType.Rgb);var bytes=new byte[info.Length];
    for(int y=0;y<h;y++)for(int x=0;x<w;x++)
    {
        double u=c*(x-500)-s*(y-500),v=s*(x-500)+c*(y-500);
        bool paper=Math.Abs(u)<=320 && Math.Abs(v)<=190;
        if(kind=="triangle")paper=paper && v>u*.5;
        byte value=paper ? (byte)240 : kind=="white-backing" ? (byte)220 : (byte)30;
        if(kind=="dark-photo" && paper)value=(byte)(55+(x+y)%35);
        if(kind=="printed-frame" && paper &&
            ((Math.Abs(u)>300 && Math.Abs(u)<305 && Math.Abs(v)<175) ||
             (Math.Abs(v)>170 && Math.Abs(v)<175 && Math.Abs(u)<305)))value=15;
        if(kind=="dust" && x==30 && y==30)value=200;
        if(kind=="exterior-mark" && x>=25 && x<35 && y>=25 && y<35)value=240;
        for(int k=0;k<3;k++)bytes[(y*w+x)*3+k]=value;
    }
    var op=new DarkBackingPageImageOp();op.Perform(bytes,info);
    if(kind=="dust")Assert(op.Frame?.Top!=null,"isolated backing dust prevents large-angle frame");
    else Assert(op.Frame?.Top==null,"ambiguous large-angle image accepted: "+kind);
    passed++;
}
Console.WriteLine($"PASS {passed} synthetic paper-frame/serialization cases; no hardware scans");
