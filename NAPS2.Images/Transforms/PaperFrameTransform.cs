namespace NAPS2.Images.Transforms;

/// <summary>
/// Rectifies parallel side edges without stretching. The rotated frame covers
/// the complete source-row interval unless confident horizontal bounds are supplied.
/// Unobserved corners are white, not invented scanner data. Kept as an undoable transform with the original image intact.
/// </summary>
public record PaperFrameTransform : Transform
{
    public PaperFrameTransform() { }
    public PaperFrameTransform(double left, double right, double slope, int width, int height)
    {
        Left = left; Right = right; Slope = slope; OriginalWidth = width; OriginalHeight = height;
    }
    public double Left { get; private set; }
    public double Right { get; private set; }
    public double Slope { get; private set; }
    /// <summary>Optional observed horizontal paper bounds; null retains all source rows.</summary>
    public double? Top { get; init; }
    public double? Bottom { get; init; }
    // Only observed, confidently fitted edges may clear exterior scanner backing.
    public double? PaperLeft { get; init; }
    public double? PaperRight { get; init; }
    public double? PaperTop { get; init; }
    public double? PaperBottom { get; init; }
    public int OriginalWidth { get; private set; }
    public int OriginalHeight { get; private set; }

    internal (double u, double v, double c, double s, int width, int height) Geometry(int width, int height)
    {
        if (OriginalWidth <= 0 || OriginalHeight <= 0 || Right <= Left || double.IsNaN(Slope) || double.IsInfinity(Slope) || Math.Abs(Slope) > 1)
            throw new InvalidOperationException("Invalid paper frame");
        double xScale = (double)width / OriginalWidth, yScale = (double)height / OriginalHeight;
        double slope = Slope * xScale / yScale;
        double c = 1 / Math.Sqrt(1 + slope * slope), s = slope * c;
        double u = Left * xScale * c, end = (Right * xScale - 1) * c;
        double v = Math.Min(s * u, s * end) / c;
        double bottom = (height - 1 + Math.Max(s * u, s * end)) / c;
        if (Top.HasValue != Bottom.HasValue || Top.HasValue && Bottom <= Top)
            throw new InvalidOperationException("Invalid horizontal paper bounds");
        if (Top.HasValue) { v = Top.Value * yScale * c; bottom = (Bottom!.Value * yScale - 1) * c; }
        return (u, v, c, s, (int)Math.Ceiling(end - u) + 1, (int)Math.Ceiling(bottom - v) + 1);
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
