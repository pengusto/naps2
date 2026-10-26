namespace NAPS2.Images.Bitwise;

/// <summary>Large-angle light-paper refinement using its convex envelope, never text orientation.</summary>
internal static class RotatedPaperRectangle
{
    internal static unsafe PaperFrameTransform? Detect(BitwiseImageData data, int[] paper,
        int[] left, int[] right)
    {
        int w = data.w, h = data.h;
        var points = new List<(double x, double y)>();
        for (int y = 0; y < h; y++)
            if (right[y] > left[y]) { points.Add((left[y], y)); points.Add((right[y], y)); }
        points = points.Distinct().OrderBy(p => p.x).ThenBy(p => p.y).ToList();
        if (points.Count < 4) return null;
        double Cross((double x, double y) a, (double x, double y) b, (double x, double y) c) =>
            (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
        var hull = new List<(double x, double y)>();
        foreach (var p in points)
        {
            while (hull.Count >= 2 && Cross(hull[hull.Count - 2], hull[hull.Count - 1], p) <= 0)
                hull.RemoveAt(hull.Count - 1);
            hull.Add(p);
        }
        int lower = hull.Count;
        for (int i = points.Count - 2; i >= 0; i--)
        {
            var p = points[i];
            while (hull.Count > lower && Cross(hull[hull.Count - 2], hull[hull.Count - 1], p) <= 0)
                hull.RemoveAt(hull.Count - 1);
            hull.Add(p);
        }
        hull.RemoveAt(hull.Count - 1);
        (double loU, double hiU, double loV, double hiV) Bounds(double angle)
        {
            double c = Math.Cos(angle), s = Math.Sin(angle);
            return (hull.Min(p => c * p.x - s * p.y), hull.Max(p => c * p.x - s * p.y),
                hull.Min(p => s * p.x + c * p.y), hull.Max(p => s * p.x + c * p.y));
        }
        double bestArea = double.MaxValue, best = 0;
        for (int i = 0; i < hull.Count; i++)
        {
            var a = hull[i]; var b = hull[(i + 1) % hull.Count];
            double angle = -Math.Atan2(b.y - a.y, b.x - a.x);
            while (angle > Math.PI / 4) angle -= Math.PI / 2;
            while (angle < -Math.PI / 4) angle += Math.PI / 2;
            if (Math.Abs(angle) < .05 || Math.Abs(angle) > Math.PI * 40 / 180) continue;
            var bounds = Bounds(angle);
            double area = (bounds.hiU - bounds.loU) * (bounds.hiV - bounds.loV);
            if (area < bestArea) { best = angle; bestArea = area; }
        }
        if (bestArea == double.MaxValue) return null;
        var g = Bounds(best);
        double width = g.hiU - g.loU, height = g.hiV - g.loV;
        if (width < 80 || height < 25 || paper.Length < bestArea * .65) return null;
        double cos = Math.Cos(best), sin = Math.Sin(best);
        // Require long observed straight edges on both perpendicular axes and
        // three of four sides. Acquisition-clipped corners need not be invented.
        var support = new double[4];
        for (int i = 0; i < hull.Count; i++)
        {
            var a = hull[i]; var b = hull[(i + 1) % hull.Count];
            double au = cos * a.x - sin * a.y, av = sin * a.x + cos * a.y;
            double bu = cos * b.x - sin * b.y, bv = sin * b.x + cos * b.y;
            double length = Math.Sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
            if (Math.Abs(au - g.loU) < 2 && Math.Abs(bu - g.loU) < 2) support[0] += length;
            if (Math.Abs(au - g.hiU) < 2 && Math.Abs(bu - g.hiU) < 2) support[1] += length;
            if (Math.Abs(av - g.loV) < 2 && Math.Abs(bv - g.loV) < 2) support[2] += length;
            if (Math.Abs(av - g.hiV) < 2 && Math.Abs(bv - g.hiV) < 2) support[3] += length;
        }
        bool[] supported = { support[0] > height * .35, support[1] > height * .35,
            support[2] > width * .35, support[3] > width * .35 };
        if (supported.Count(x => x) < 3 || !supported.Take(2).Any(x => x) || !supported.Skip(2).Any(x => x))
            return null;
        const double margin = 3;
        long exterior = 0, backing = 0;
        var dust = new HashSet<int>();
        for (int y = 0; y < h; y++)
        {
            var row = data.ptr + (data.invertY ? h - 1 - y : y) * data.stride;
            for (int x = 0; x < w; x++)
            {
                double u = cos * x - sin * y, v = sin * x + cos * y;
                if (u >= g.loU - margin && u <= g.hiU + margin &&
                    v >= g.loV - margin && v <= g.hiV + margin) continue;
                var p = row + x * data.bytesPerPixel;
                int r = p[data.rOff], green = p[data.gOff], b = p[data.bOff];
                int value = (299 * r + 587 * green + 114 * b) / 1000;
                exterior++;
                // Disconnected light margins/marks must veto a rectangle fitted
                // to an interior white region (e.g. inside a printed frame).
                if (value > 160 || Math.Max(r, Math.Max(green, b)) - Math.Min(r, Math.Min(green, b)) > 100)
                {
                    dust.Add(y * w + x);
                    if (dust.Count > Math.Max(16, paper.Length / 10000)) return null;
                }
                if (value < 100) backing++;
            }
        }
        // Permit only a few isolated bright scanner-dust pixels. A connected
        // exterior margin/mark (including the outside of a printed frame) vetoes.
        while (dust.Count > 0)
        {
            int count = 0; var pending = new Stack<int>();
            int seed = dust.First(); dust.Remove(seed); pending.Push(seed);
            while (pending.Count > 0)
            {
                int n = pending.Pop();
                if (++count >= 16) return null;
                for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++)
                {
                    int x = n % w + dx, y = n / w + dy;
                    if (x >= 0 && x < w && y >= 0 && y < h && dust.Remove(y * w + x)) pending.Push(y * w + x);
                }
            }
        }
        if (exterior < (long)w * h * .05 || backing < exterior * .98) return null;
        // Enclose all observed paper, never an inscribed crop. Fill only outside
        // that complete envelope; the additional canvas margin remains white.
        return new PaperFrameTransform((g.loU - margin) / cos, (g.hiU + margin + 1) / cos,
            Math.Tan(best), w, h)
        { Top = (g.loV - margin) / cos, Bottom = (g.hiV + margin + 1) / cos,
          PaperLeft = (g.loU - .5) / cos, PaperRight = (g.hiU + 1.5) / cos,
          PaperTop = (g.loV - .5) / cos, PaperBottom = (g.hiV + 1.5) / cos };
    }
}
