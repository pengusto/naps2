namespace NAPS2.Images.Bitwise;

/// <summary>
/// A restricted ES-60W light-paper detector. Uses the connected paper surface,
/// not text orientation. Two perpendicular observed edges must agree; uncertain
/// edge-printed pages retain the existing conservative framing path.
/// </summary>
internal static class DarkBackingRectangleDetector
{
    internal static unsafe PaperFrameTransform? Detect(BitwiseImageData data)
    {
        // Keep the established width-only decision: distant scanner padding is
        // not used as evidence for the horizontal/rotation refinement.
        var width = new DarkBackingWidthImageOp(); width.Perform(data);
        var region = data;
        region.ptr += width.Left * data.bytesPerPixel;
        region.w -= width.Left + width.Right;
        var frame = DetectRegion(region);
        if (frame == null) return null;
        double offset = width.Left;
        return new PaperFrameTransform(frame.Left + offset, frame.Right + offset, frame.Slope, data.w, data.h)
        {
            Top = frame.Top + frame.Slope * offset, Bottom = frame.Bottom + frame.Slope * offset,
            PaperLeft = frame.PaperLeft + offset, PaperRight = frame.PaperRight + offset,
            PaperTop = frame.PaperTop + frame.Slope * offset, PaperBottom = frame.PaperBottom + frame.Slope * offset
        };
    }

    private static unsafe PaperFrameTransform? DetectRegion(BitwiseImageData data)
    {
        int w = data.w, h = data.h;
        // Bound additional scratch memory; unusually long scans use the existing path.
        if ((long)w * h > 20_000_000 || w < 100 || h < 30 || data.bytesPerPixel is not (3 or 4) || data.invertColorSpace) return null;
        var mask = new byte[checked(w * h)];
        for (int y = 0; y < h; y++)
        {
            var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
            for (int x = 0; x < w; x++)
            {
                var p = row + x * data.bytesPerPixel;
                if ((299 * p[data.rOff] + 587 * p[data.gOff] + 114 * p[data.bOff]) / 1000 > 160)
                    mask[y * w + x] = 1;
            }
        }
        // Find the connected white paper, ignoring isolated backing dust.
        var queue = new int[mask.Length];
        int[] paper = Array.Empty<int>();
        for (int seed = 0; seed < mask.Length; seed++)
        {
            if (mask[seed] != 1) continue;
            int count = 1; queue[0] = seed; mask[seed] = 2;
            for (int at = 0; at < count; at++)
            {
                int n = queue[at], x = n % w;
                void Add(int next)
                {
                    if (mask[next] != 1) return;
                    mask[next] = 2; queue[count++] = next;
                }
                if (x > 0) Add(n - 1);
                if (x + 1 < w) Add(n + 1);
                if (n >= w) Add(n - w);
                if (n + w < mask.Length) Add(n + w);
            }
            if (count > paper.Length) { paper = new int[count]; Array.Copy(queue, paper, count); }
        }
        if (paper.Length < (long)w * h * .12) return null;
        var left = Enumerable.Repeat(w, h).ToArray(); var right = new int[h];
        var top = Enumerable.Repeat(h, w).ToArray(); var bottom = new int[w];
        foreach (int n in paper)
        {
            int x = n % w, y = n / w;
            left[y] = Math.Min(left[y], x); right[y] = Math.Max(right[y], x);
            top[x] = Math.Min(top[x], y); bottom[x] = Math.Max(bottom[x], y);
        }
        var rotated = RotatedPaperRectangle.Detect(data, paper, left, right);
        if (rotated != null) return rotated;
        int minX = paper.Min(n => n % w), maxX = paper.Max(n => n % w);
        int minY = paper.Min(n => n / w), maxY = paper.Max(n => n / w);
        if (maxX - minX < 80 || maxY - minY < 25 ||
            paper.Length < (maxX - minX) * (double)(maxY - minY) * .65) return null;
        var vertical = new[] { Fit(left, minY, maxY, w), Fit(right, minY, maxY, w) }
            .Where(x => x != null).Select(x => x!.Value).ToArray();
        var horizontal = new[] { Fit(top, minX, maxX, h), Fit(bottom, minX, maxX, h) }
            .Where(x => x != null).Select(x => x!.Value).ToArray();
        if (vertical.Length == 0 || horizontal.Length == 0) return null;
        double vs = vertical[0], hs = horizontal[0];
        if (vertical.Any(x => Math.Abs(x - vs) > .006) || horizontal.Any(x => Math.Abs(x - hs) > .006) ||
            Math.Abs(vs + hs) > .006) return null;
        double slope = (vs - hs) / 2;
        if (Math.Abs(slope) > .05) return null;
        if (Math.Abs(slope) < .0005) slope = 0;
        double c = 1 / Math.Sqrt(1 + slope * slope), s = slope * c;
        double loU = double.MaxValue, hiU = double.MinValue, loV = double.MaxValue, hiV = double.MinValue;
        foreach (int n in paper)
        {
            int x = n % w, y = n / w;
            double u = c * x - s * y, v = s * x + c * y;
            loU = Math.Min(loU, u); hiU = Math.Max(hiU, u);
            loV = Math.Min(loV, v); hiV = Math.Max(hiV, v);
        }
        double? Edge(int[] values, int first, int last, int limit, bool horizontalEdge)
        {
            if (Fit(values, first, last, limit) == null) return null;
            return Median(Enumerable.Range(first, last - first + 1)
                .Where(i => values[i] > 2 && values[i] < limit - 3)
                .Select(i => horizontalEdge ? values[i] + slope * i : values[i] - slope * i).ToList());
        }
        double? pl = Edge(left, minY, maxY, w, false), pr = Edge(right, minY, maxY, w, false);
        double? pt = Edge(top, minX, maxX, h, true), pb = Edge(bottom, minX, maxX, h, true);
        // A half-pixel outward allowance keeps the observed paper edge.
        pl -= .5; pr += .5; pt -= .5; pb += .5;
        // Check every pixel of the established width region, not just sampled
        // rows. Light or saturated exterior marks veto this refinement.
        int outside = 0;
        for (int y = 0; y < h; y++)
        {
            var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
            for (int x = 0; x < w; x++)
            {
                double u = c * x - s * y, v = s * x + c * y;
                var p = row + x * data.bytesPerPixel;
                int r = p[data.rOff], g = p[data.gOff], b = p[data.bOff];
                int value = (299 * r + 587 * g + 114 * b) / 1000;
                if (u < loU - 2 || u > hiU + 2 || v < loV - 2 || v > hiV + 2)
                {
                    outside++;
                    if (value >= 160 || Math.Max(r, Math.Max(g, b)) - Math.Min(r, Math.Min(g, b)) >= 100)
                        return null;
                }
                // Whitening outside the fitted rectangle may cover paper-corner
                // whitespace, but must not cover dark print inside its observed
                // row/column envelope. If that happens, leave the source alone.
                bool cleared = (pl.HasValue && u < pl * c) || (pr.HasValue && u >= pr * c) ||
                               (pt.HasValue && v < pt * c) || (pb.HasValue && v >= pb * c);
                if (cleared && value < 140 && x > left[y] + 1 && x < right[y] - 1 &&
                    y > top[x] + 1 && y < bottom[x] - 1) return null;
                // Do not infer a blank edge through near-edge print. Clipped
                // acquisition edges are exempt: they are retained in full.
                else if (value < 100 && x > left[y] + 1 && x < right[y] - 1 &&
                    y > top[x] + 1 && y < bottom[x] - 1 && u > loU + 1 && u < hiU - 1 && v > loV + 1 && v < hiV - 1 &&
                    ((minX > 2 && u < loU + 5) || (maxX < w - 3 && u > hiU - 5) ||
                     (minY > 2 && v < loV + 5) || (maxY < h - 3 && v > hiV - 5))) return null;
            }
        }
        if (outside < Math.Max(w, h) * 2) return null;
        // Keep an outward safety pixel for the paper edge and interpolation.
        return new PaperFrameTransform((loU - 1) / c, (hiU + 2) / c, slope, w, h)
        { Top = (loV - 1) / c, Bottom = (hiV + 2) / c,
          PaperLeft = pl, PaperRight = pr, PaperTop = pt, PaperBottom = pb };
    }

    // Robust line fit, excluding scan-clipped edges and narrow protrusions.
    private static double? Fit(int[] edge, int first, int last, int limit)
    {
        int step = Math.Max(1, (last - first) / 150);
        var points = new List<(double x, double y)>();
        for (int i = first; i <= last; i += step)
            if (edge[i] > 2 && edge[i] < limit - 3) points.Add((i, edge[i]));
        if (points.Count < 15 || points.Last().x - points.First().x < (last - first) * .35) return null;
        var slopes = new List<double>();
        foreach (var a in points) foreach (var b in points)
            if (b.x - a.x > (last - first) * .3) slopes.Add((b.y - a.y) / (b.x - a.x));
        if (slopes.Count == 0) return null;
        double slope = Median(slopes), intercept = Median(points.Select(p => p.y - slope * p.x).ToList());
        var good = points.Where(p => Math.Abs(p.y - intercept - slope * p.x) <= 1.5).ToArray();
        if (good.Length < points.Count * .85 || Math.Abs(slope) > .05) return null;
        double mx = good.Average(p => p.x), my = good.Average(p => p.y);
        return good.Sum(p => (p.x - mx) * (p.y - my)) / good.Sum(p => (p.x - mx) * (p.x - mx));
    }

    private static double Median(List<double> values)
    {
        values.Sort(); int n = values.Count;
        return n % 2 == 0 ? (values[n / 2 - 1] + values[n / 2]) / 2 : values[n / 2];
    }
}
