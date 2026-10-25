namespace NAPS2.Images.Bitwise;

/// <summary>
/// Fits two approximately parallel light-paper edges on dark scanner backing.
/// No paper-height estimate: the frame includes the entire received row range.
/// Ambiguous images deliberately have no frame.
/// </summary>
internal class DarkBackingPageImageOp : UnaryBitwiseImageOp
{
    public PaperFrameTransform? Frame { get; private set; }
    protected override LockMode LockMode => LockMode.ReadOnly;
    protected override int GetPartitionCount(BitwiseImageData data) => 1;
    protected override void ValidateCore(BitwiseImageData data) { }

    protected override unsafe void PerformCore(BitwiseImageData data, int partStart, int partEnd)
    {
        Frame = null;
        int w = data.w, h = data.h;
        if (w < 100 || h < 30 || data.invertColorSpace || data.bytesPerPixel is not (3 or 4)) return;
        var points = new List<(int y, int left, int right)>();
        var envelope = new List<(int y, int left, int right)>();
        int rows = Math.Min(h, 400);
        int[] luma = new int[w];
        for (int sample = 0; sample < rows; sample++)
        {
            int y = (int)((2L * sample + 1) * h / (2 * rows));
            var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
            int first = -1, last = -1, run = 0;
            for (int x = 0; x < w; x++)
            {
                var p = row + x * data.bytesPerPixel;
                luma[x] = (299 * p[data.rOff] + 587 * p[data.gOff] + 114 * p[data.bOff]) / 1000;
                run = luma[x] > 140 ? run + 1 : 0;
                if (run >= 5)
                {
                    if (first < 0) first = x - 4;
                    last = x + 1;
                }
            }
            if (first < 0 || last - first < w * .1) continue;
            envelope.Add((y, first, last));
            int light = 0;
            for (int x = first; x < last; x++) if (luma[x] > 140) light++;
            if (light >= (last - first) * .5) points.Add((y, first, last));
        }
        if (points.Count < rows * .35) return;

        (double intercept, double slope)? Fit(bool right)
        {
            double X((int y, int left, int right) p) => right ? p.right : p.left;
            var slopes = new List<double>();
            for (int i = 0; i < points.Count; i++)
                for (int j = i + 1; j < points.Count; j++)
                    if (points[j].y - points[i].y >= h * .25)
                        slopes.Add((X(points[j]) - X(points[i])) / (points[j].y - points[i].y));
            if (slopes.Count == 0) return null;
            double b = Median(slopes), a = Median(points.Select(p => X(p) - b * p.y).ToList());
            var inliers = points.Where(p => Math.Abs(X(p) - a - b * p.y) <= Math.Max(2, w * .002)).ToList();
            if (inliers.Count < points.Count * .6 || inliers.Last().y - inliers.First().y < h * .5) return null;
            double meanY = inliers.Average(p => p.y), meanX = inliers.Average(X);
            double denominator = inliers.Sum(p => (p.y - meanY) * (p.y - meanY));
            if (denominator <= 0) return null;
            b = inliers.Sum(p => (p.y - meanY) * (X(p) - meanX)) / denominator;
            return (meanX - b * meanY, b);
        }
        var leftFit = Fit(false); var rightFit = Fit(true);
        if (leftFit == null || rightFit == null ||
            Math.Abs(leftFit.Value.slope - rightFit.Value.slope) > .004) return;
        double slope = (leftFit.Value.slope + rightFit.Value.slope) / 2;
        if (Math.Abs(slope) > .05) return;
        if (Math.Abs(slope) < .0005) slope = 0;
        // Use the OUTERMOST observations, not the fit's central estimate. This
        // retains bright content where the paper bends or a fitted edge is noisy.
        double margin = Math.Max(3, w * .0015);
        double left = envelope.Min(p => p.left - slope * p.y) - margin;
        double rightEdge = envelope.Max(p => p.right - slope * p.y) + margin;
        if (rightEdge - left < w * .1 || rightEdge - left > w * 1.02) return;

        long outside = 0, dark = 0;
        for (int sample = 0; sample < rows; sample++)
        {
            int y = (int)((2L * sample + 1) * h / (2 * rows));
            var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
            for (int x = 0; x < w; x++)
            {
                if (x >= left + slope * y && x < rightEdge + slope * y) continue;
                var p = row + x * data.bytesPerPixel;
                int r = p[data.rOff], g = p[data.gOff], b = p[data.bOff];
                int value = (299 * r + 587 * g + 114 * b) / 1000;
                outside++;
                if (value < 100 && Math.Max(r, Math.Max(g, b)) - Math.Min(r, Math.Min(g, b)) < 45) dark++;
            }
        }
        // Require observable neutral dark backing. A full-width page is a no-op.
        if (outside < rows * Math.Max(4, w * .002) || dark < outside * .995) return;
        if (slope == 0) { left = Math.Max(0, Math.Floor(left)); rightEdge = Math.Min(w, Math.Ceiling(rightEdge)); }
        Frame = new PaperFrameTransform(left, rightEdge, slope, w, h);
    }

    private static double Median(List<double> values)
    {
        values.Sort();
        int n = values.Count;
        return n % 2 == 0 ? (values[n / 2 - 1] + values[n / 2]) / 2 : values[n / 2];
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
