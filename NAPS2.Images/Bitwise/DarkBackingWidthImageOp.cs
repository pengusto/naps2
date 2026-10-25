namespace NAPS2.Images.Bitwise;

/// <summary>
/// Experimental width-only detector for light paper on the ES-60W's dark backing.
/// Ambiguous/full-width images are preserved. Never infers height from blank pixels.
/// </summary>
internal class DarkBackingWidthImageOp : UnaryBitwiseImageOp
{
    public int Left { get; private set; }
    public int Right { get; private set; }
    protected override LockMode LockMode => LockMode.ReadOnly;
    protected override int GetPartitionCount(BitwiseImageData data) => 1;
    protected override void ValidateCore(BitwiseImageData data) { }

    protected override unsafe void PerformCore(BitwiseImageData data, int partStart, int partEnd)
    {
        DetectLight(data);
        if (Left == 0 && Right == 0) (Left, Right) = PhotoBackingWidthDetector.Detect(data);
    }

    private unsafe void DetectLight(BitwiseImageData data)
    {
        Left = Right = 0;
        if (data.w < 100 || data.h < 30 || data.invertColorSpace || data.bytesPerPixel is not (3 or 4)) return;
        int rows = Math.Min(data.h, 400);
        var light = new int[data.w];
        var dark = new int[data.w];
        for (int sample = 0; sample < rows; sample++)
        {
            int y = (int)((2L * sample + 1) * data.h / (2 * rows));
            if (data.invertY) y = data.h - 1 - y;
            var row = data.ptr + y * data.stride;
            for (int x = 0; x < data.w; x++)
            {
                var p = row + x * data.bytesPerPixel;
                int luma = (299 * p[data.rOff] + 587 * p[data.gOff] + 114 * p[data.bOff]) / 1000;
                if (luma > 140) light[x]++;
                if (luma < 100) dark[x]++;
            }
        }
        int first = Array.FindIndex(light, n => n * 10 >= rows);
        int last = Array.FindLastIndex(light, n => n * 10 >= rows);
        int span = last - first + 1;
        if (first < 0 || span < data.w * .1 || span >= data.w * .97) return;
        long paperLight = 0;
        for (int x = first; x <= last; x++) paperLight += light[x];
        if (paperLight < (long)span * rows * .5) return;
        int margin = Math.Max(8, (int)Math.Ceiling(data.w * .005));
        int left = Math.Max(0, first - margin);
        int end = Math.Min(data.w, last + 1 + margin);
        bool IsBacking(int start, int stop)
        {
            if (stop - start < data.w * .02) return false;
            long count = 0;
            for (int x = start; x < stop; x++) count += dark[x];
            return count >= (long)(stop - start) * rows * .99;
        }
        // A narrow scanner-edge fringe is retained rather than treated as a crop.
        if (left < data.w * .02) left = 0;
        if (data.w - end < data.w * .02) end = data.w;
        if (left > 0 && !IsBacking(0, left) || end < data.w && !IsBacking(end, data.w)) return;
        Left = left;
        Right = data.w - end;
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
